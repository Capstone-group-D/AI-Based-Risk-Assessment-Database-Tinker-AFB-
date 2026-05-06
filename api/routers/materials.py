"""
materials.py — AUL Materials, Shop Authorization, and Material PPE Recommendation Endpoints

Exposes the materials, shops, and material_authorizations tables that were
populated from the Tinker AFB AUL CSV.  Returns empty lists gracefully when
the CSV has not been imported yet.

The /api/v1/materials/{msn}/recommend-ppe endpoint ties AUL data directly into
the PPE recommendation engine: it looks up the material by MSN, fuzzy-matches
the material noun against the known hazard catalog, then delegates to the same
recommend_ppe logic used by the NLP pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from thefuzz import process as fuzz_process

from db.session import get_db
from schemas import MaterialItem, ShopItem, MaterialAuthorizationItem, MaterialPPERequest, MaterialPPEResponse

router = APIRouter()


@router.get("/api/v1/materials", response_model=List[MaterialItem])
def list_materials(q: Optional[str] = None, db=Depends(get_db)):
    """Returns AUL materials, with optional full-text search on noun or MSN.

    Capped at 200 rows per call to keep responses snappy.
    """
    if q:
        rows = db.execute(
            """SELECT msn, noun, bulk_issue FROM materials
               WHERE noun LIKE ? OR msn LIKE ?
               ORDER BY noun LIMIT 200""",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT msn, noun, bulk_issue FROM materials ORDER BY noun LIMIT 200").fetchall()

    return [MaterialItem(msn=r["msn"], noun=r["noun"], bulk_issue=bool(r["bulk_issue"])) for r in rows]


@router.get("/api/v1/materials/{msn}/authorizations", response_model=List[MaterialAuthorizationItem])
def get_material_authorizations(msn: str, db=Depends(get_db)):
    """Returns all shop authorizations for a given material (by MSN)."""
    rows = db.execute(
        """SELECT id, msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand
           FROM material_authorizations
           WHERE msn = ?
           ORDER BY shop_code""",
        (msn,),
    ).fetchall()
    return [MaterialAuthorizationItem(**row) for row in rows]


@router.get("/api/v1/shops", response_model=List[ShopItem])
def list_shops(db=Depends(get_db)):
    """Returns all shops from the AUL reference table."""
    rows = db.execute("SELECT shop_code, org_symbol FROM shops ORDER BY shop_code").fetchall()
    return [ShopItem(**row) for row in rows]


@router.post("/api/v1/materials/recommend-ppe", response_model=MaterialPPEResponse)
def recommend_ppe_for_material(payload: MaterialPPERequest, db=Depends(get_db)):
    """
    Looks up a hazardous material by MSN, fuzzy-matches its name against the
    known hazard catalog, then returns PPE and engineering control recommendations
    using the same engine as the NLP analyze-task pipeline.

    This is the primary integration point between the AUL authorization data
    and the AI recommendation engine.
    """
    from routers.safety_records import recommend_ppe, _get_all_safety_records
    from schemas import PPERecommendationRequest

    # Fetch the material
    mat_row = db.execute("SELECT msn, noun FROM materials WHERE msn = ?", (payload.msn,)).fetchone()
    if not mat_row:
        raise HTTPException(status_code=404, detail=f"Material MSN '{payload.msn}' not found")

    material_name = mat_row["noun"]

    # Fuzzy-match the material noun against hazard labels
    hazard_rows = db.execute("SELECT hazard_id, hazard_label FROM hazards").fetchall()
    hazard_map = {row["hazard_label"]: row["hazard_id"] for row in hazard_rows}

    matched_hazard_id = None
    matched_hazard_label = None

    if hazard_map:
        match_label, score = fuzz_process.extractOne(material_name, list(hazard_map.keys()))
        if score >= 40:
            matched_hazard_id = hazard_map[match_label]
            matched_hazard_label = match_label

    # Also check if any authorized process names match known work_types
    auth_rows = db.execute(
        "SELECT DISTINCT process_name FROM material_authorizations WHERE msn = ? AND process_name IS NOT NULL",
        (payload.msn,),
    ).fetchall()
    process_names = [r["process_name"] for r in auth_rows if r["process_name"]]

    best_process = None
    if process_names:
        known_processes = [
            r["work_type"]
            for r in db.execute("SELECT DISTINCT work_type FROM safety_records").fetchall()
            if r["work_type"]
        ]
        if known_processes:
            combined_query = " ".join(process_names)
            match_proc, proc_score = fuzz_process.extractOne(combined_query, known_processes)
            if proc_score >= 40:
                best_process = match_proc

    # Need at least one dimension to recommend
    if not matched_hazard_id and not best_process:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Could not map material '{material_name}' (MSN: {payload.msn}) to a known hazard or process. "
                "Ensure the hazard catalog and safety records are populated."
            ),
        )

    req = PPERecommendationRequest(
        material_id=matched_hazard_id,
        process_type=best_process,
        severity_level=payload.severity_level,
    )

    try:
        result = recommend_ppe(req, db)
    except HTTPException:
        # If combined fails, try dimensions separately
        if matched_hazard_id and best_process:
            try:
                result = recommend_ppe(
                    PPERecommendationRequest(material_id=matched_hazard_id, severity_level=payload.severity_level), db
                )
            except HTTPException:
                result = recommend_ppe(
                    PPERecommendationRequest(process_type=best_process, severity_level=payload.severity_level), db
                )
        else:
            raise

    # Fetch authorized shop codes for this material
    shop_rows = db.execute(
        "SELECT DISTINCT shop_code FROM material_authorizations WHERE msn = ?", (payload.msn,)
    ).fetchall()
    authorized_shops = [r["shop_code"] for r in shop_rows]

    return MaterialPPEResponse(
        msn=payload.msn,
        material_name=material_name,
        matched_hazard_label=matched_hazard_label,
        authorized_shops=authorized_shops,
        **result.model_dump(),
    )
