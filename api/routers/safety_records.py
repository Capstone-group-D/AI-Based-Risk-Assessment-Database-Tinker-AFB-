from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import json
import uuid
from datetime import datetime
from schemas import (
    SafetyRecord,
    PPEItem,
    PPERecommendationRequest,
    TaskAnalysisRequest,
    RecommendedPPEItem,
    EngineeringControlItem,
    PPERecommendationResponse,
    TaskAnalysisResponse,
)
from db.session import get_db
from nlp.analyzer import analyze_task_description

router = APIRouter()

SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3, "Severe": 4}

ENGINEERING_CONTROL_RULES = {
    "Chemical": [
        EngineeringControlItem(
            control_type="Local Exhaust Ventilation",
            rationale="Capture chemical vapors/aerosols at the source per industrial hygiene best practices.",
        ),
        EngineeringControlItem(
            control_type="Closed Transfer / Secondary Containment",
            rationale="Reduce splash and spill potential during handling and transfer of hazardous liquids.",
        ),
    ],
    "Gas": [
        EngineeringControlItem(
            control_type="Continuous Gas Monitoring",
            rationale="Provide real-time detection and alarms for oxygen displacement/toxic gas accumulation.",
        ),
        EngineeringControlItem(
            control_type="Pressure Regulation and Relief",
            rationale="Minimize release risk by controlling line pressure and overpressure events.",
        ),
    ],
    "Particulate": [
        EngineeringControlItem(
            control_type="HEPA-Filtered Negative Pressure Enclosure",
            rationale="Contain and remove fine particulates (e.g., lead/asbestos) from breathing zones.",
        ),
        EngineeringControlItem(
            control_type="Wet Methods / Dust Suppression",
            rationale="Lower airborne particle generation during disturbance or cleanup activities.",
        ),
    ],
}


def _get_all_safety_records(db) -> List[SafetyRecord]:
    """Helper method to fetch all safety records from SQLite and construct Pydantic models."""
    records_query = '''
        SELECT sr.*, h.hazard_label, h.hazard_category
        FROM safety_records sr
        JOIN hazards h ON sr.hazard_id = h.hazard_id
    '''
    rows = db.execute(records_query).fetchall()
    
    ppe_query = '''
        SELECT srp.record_id, p.ppe_id, p.ppe_label, p.ppe_category
        FROM safety_record_ppe srp
        JOIN ppe p ON srp.ppe_id = p.ppe_id
    '''
    ppe_rows = db.execute(ppe_query).fetchall()
    
    ppe_map = {}
    for r in ppe_rows:
        ppe_map.setdefault(r['record_id'], []).append({
            'ppe_id': r['ppe_id'],
            'ppe_label': r['ppe_label'],
            'ppe_category': r['ppe_category']
        })
        
    safety_records = []
    for row in rows:
        row_dict = dict(row)
        row_dict['ppe_required'] = ppe_map.get(row['record_id'], [])
        # Pydantic handles parsing
        safety_records.append(SafetyRecord(**row_dict))
        
    return safety_records


@router.get("/api/v1/health")
def health_check():
    """Health check endpoint — used by the frontend header to probe connectivity."""
    return {"status": "ok", "message": "API online", "version": "0.1.0"}


@router.get("/api/v1/safety-records", response_model=List[SafetyRecord])
def list_safety_records(db = Depends(get_db)):
    """Returns the complete list of safety records in the database."""
    return _get_all_safety_records(db)


@router.get("/api/v1/safety-records/{record_id}", response_model=SafetyRecord)
def get_safety_record(record_id: str, db = Depends(get_db)):
    """Returns a single safety record by its record ID."""
    records = _get_all_safety_records(db)
    for record in records:
        if record.record_id == record_id:
            return record
    raise HTTPException(status_code=404, detail=f"Safety record {record_id} not found")


@router.post("/api/recommend-ppe", response_model=PPERecommendationResponse)
def recommend_ppe(payload: PPERecommendationRequest, db = Depends(get_db)):
    """
    Recommends PPE + engineering controls from SDS-like record patterns and
    severity thresholds derived from historical safety records.
    """
    matched_records = _get_all_safety_records(db)

    if payload.material_id:
        matched_records = [
            record for record in matched_records if record.hazard_id.lower() == payload.material_id.lower()
        ]

    if payload.process_type:
        process_query = payload.process_type.lower()
        matched_records = [
            record for record in matched_records if process_query in record.work_type.lower()
        ]

    if not matched_records:
        raise HTTPException(status_code=404, detail="No matching hazard/process records found")

    if payload.severity_level:
        normalized = payload.severity_level.capitalize()
        if normalized not in SEVERITY_RANK:
            raise HTTPException(status_code=400, detail="severity_level must be one of: Low, Moderate, High, Severe")
        severity_basis = normalized
    else:
        severity_basis = max(matched_records, key=lambda row: SEVERITY_RANK[row.exposure_level]).exposure_level

    minimum_rank = SEVERITY_RANK[severity_basis]
    severity_filtered = [
        record for record in matched_records if SEVERITY_RANK[record.exposure_level] >= minimum_rank
    ]

    ppe_catalog: Dict[str, RecommendedPPEItem] = {}
    for record in severity_filtered:
        for ppe in record.ppe_required:
            if ppe.ppe_id not in ppe_catalog:
                ppe_catalog[ppe.ppe_id] = RecommendedPPEItem(
                    ppe_id=ppe.ppe_id,
                    ppe_type=ppe.ppe_label,
                    ppe_category=ppe.ppe_category,
                    rationale=(
                        f"Recommended for {record.hazard_label} during {record.work_type} "
                        f"at {record.exposure_level} severity based on historical SDS-aligned controls."
                    ),
                )

    engineering_controls: Dict[str, EngineeringControlItem] = {}
    for record in severity_filtered:
        for control in ENGINEERING_CONTROL_RULES.get(record.hazard_category, []):
            engineering_controls[control.control_type] = control

    return PPERecommendationResponse(
        criteria={
            "material_id": payload.material_id,
            "process_type": payload.process_type,
            "severity_level": payload.severity_level,
        },
        severity_basis=severity_basis,
        ppe_recommendations=list(ppe_catalog.values()),
        engineering_controls=list(engineering_controls.values()),
    )

def _persist_ai_assessment(db, task_description: str, response: PPERecommendationResponse) -> str:
    assessment_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    db.execute(
        """
        INSERT INTO ai_assessments (assessment_id, created_at, task_description, response_json)
        VALUES (?, ?, ?, ?)
        """,
        (assessment_id, created_at, task_description, json.dumps(response.model_dump())),
    )
    db.commit()
    return assessment_id


@router.post("/api/v1/analyze-task", response_model=TaskAnalysisResponse)
def analyze_task(payload: TaskAnalysisRequest, db = Depends(get_db)):
    """
    Analyzes a natural language description to extract intent and forwards
    the inferred hazards/processes to the standard PPE recommendation engine.
    """
    hazard_id, process_type = analyze_task_description(payload.task_description, db)
    
    if not hazard_id and not process_type:
        raise HTTPException(status_code=400, detail="Could not confidently extract hazards or processes from the description. Please be more specific.")
        
    req = PPERecommendationRequest(
        material_id=hazard_id,
        process_type=process_type,
        severity_level=payload.severity_level
    )
    
    try:
        result = recommend_ppe(req, db)
        assessment_id = _persist_ai_assessment(db, payload.task_description, result)
        return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
    except HTTPException:
        # Fallback to single dimension if combined matching returns 0 records
        if hazard_id and process_type:
            try:
                fallback_req = PPERecommendationRequest(material_id=hazard_id, severity_level=payload.severity_level)
                result = recommend_ppe(fallback_req, db)
                assessment_id = _persist_ai_assessment(db, payload.task_description, result)
                return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
            except HTTPException:
                try:
                    fallback_req = PPERecommendationRequest(process_type=process_type, severity_level=payload.severity_level)
                    result = recommend_ppe(fallback_req, db)
                    assessment_id = _persist_ai_assessment(db, payload.task_description, result)
                    return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
                except HTTPException:
                    raise
        raise
