from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import json
import uuid
from datetime import datetime
from core.auth import require_role
from schemas import (
    SafetyRecord,
    SafetyRecordCreate,
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

# Engineering control rules keyed by hazard_category.
# Contains both the original synthetic-data categories and the real seed-data categories
# so that tests and production data both resolve correctly.
ENGINEERING_CONTROL_RULES = {
    # ── Real seed-data categories ────────────────────────────────────────────
    "Chemical & Airborne": [
        EngineeringControlItem(
            control_type="Local Exhaust Ventilation",
            rationale="Capture chemical vapors, fumes, and aerosols at the source per industrial hygiene best practices.",
        ),
        EngineeringControlItem(
            control_type="Closed Transfer / Secondary Containment",
            rationale="Reduce splash and spill potential during handling and transfer of hazardous materials.",
        ),
    ],
    "Physical Environment": [
        EngineeringControlItem(
            control_type="Noise Monitoring & Hearing Conservation Program",
            rationale="Control noise exposures per OSHA 1910.95; implement administrative controls and hearing protection.",
        ),
        EngineeringControlItem(
            control_type="Environmental Controls (HVAC / Heat Stress Monitoring)",
            rationale="Monitor and control temperature extremes; provide cooling stations and hydration per thermal stress guidelines.",
        ),
    ],
    "Mechanical & Equipment": [
        EngineeringControlItem(
            control_type="Lockout/Tagout (LOTO) Procedures",
            rationale="Control hazardous energy release during maintenance per OSHA 1910.147.",
        ),
        EngineeringControlItem(
            control_type="Machine Guarding",
            rationale="Prevent contact with moving parts through fixed or interlocked guards per OSHA 1910.212.",
        ),
    ],
    "Slips, Trips, Falls & Work at Height": [
        EngineeringControlItem(
            control_type="Fall Protection System",
            rationale="Provide guardrails, safety nets, or personal fall arrest systems for elevated work per OSHA 1926.502.",
        ),
        EngineeringControlItem(
            control_type="Walking Surface Management",
            rationale="Maintain clear, dry, and marked walking surfaces; use anti-slip coatings where appropriate.",
        ),
    ],
    "Ergonomics & Human Factors": [
        EngineeringControlItem(
            control_type="Ergonomic Job Hazard Analysis",
            rationale="Evaluate and redesign tasks to reduce repetitive motion, awkward postures, and excessive force.",
        ),
        EngineeringControlItem(
            control_type="Mechanical Lifting Assists",
            rationale="Use hoists, lift tables, or carts to eliminate manual material handling above threshold weights.",
        ),
    ],
    "Sharp Objects": [
        EngineeringControlItem(
            control_type="Sharps Management Program",
            rationale="Implement safe handling, storage, and disposal procedures for sharp-edged tools and materials.",
        ),
    ],
    "Biological": [
        EngineeringControlItem(
            control_type="Pest Control / Site Hazard Assessment",
            rationale="Survey work areas for biological hazards; implement control measures per site safety protocols.",
        ),
    ],
    # ── Legacy synthetic-data categories (kept for test backward-compat) ─────
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


# Tinker AFB procedural controls sourced directly from Risk Assess Form.pdf
# (risk_assessment_form.json → controls_and_requirements).  Keyed by hazard_id
# so each matched hazard surfaces only the controls that are relevant to it.
TINKER_PROCEDURAL_CONTROLS_BY_HAZARD_ID: Dict[str, List[EngineeringControlItem]] = {
    # ── Lockout / Tagout ────────────────────────────────────────────────────
    "haz_electrical_mechanical_energy": [
        EngineeringControlItem(
            control_id="ctl_form_493", source="TINKER",
            control_type="LOTO — Form 493",
            rationale="Complete Tinker AFB Form 493 Lockout/Tagout before any maintenance on electrical or mechanical energy sources.",
        ),
        EngineeringControlItem(
            control_id="ctl_depressure_drain", source="TINKER",
            control_type="LOTO — Depressure/Drain",
            rationale="Depressurize and drain all hydraulic and pneumatic lines before accessing equipment.",
        ),
    ],
    "haz_gravity_potential_energy": [
        EngineeringControlItem(
            control_id="ctl_block_shore_all_suspended_loads", source="TINKER",
            control_type="LOTO — Block/Shore all Suspended Loads",
            rationale="Block or shore all suspended loads to prevent uncontrolled lowering before working beneath them.",
        ),
        EngineeringControlItem(
            control_id="ctl_crane_hoist_inspection", source="TINKER",
            control_type="Crane/Hoist Inspection",
            rationale="Perform pre-use inspection of crane and hoist equipment per Tinker AFB Material Handling Equipment requirements.",
        ),
        EngineeringControlItem(
            control_id="ctl_rigging_sling_chain_inspection", source="TINKER",
            control_type="Rigging Sling/Chain Inspection",
            rationale="Inspect all rigging slings and chains for damage, deformation, or wear before lifting operations.",
        ),
    ],
    "haz_heavy_load_secure": [
        EngineeringControlItem(
            control_id="ctl_block_shore_all_suspended_loads", source="TINKER",
            control_type="LOTO — Block/Shore all Suspended Loads",
            rationale="Block or shore all suspended loads before working in the load path or beneath them.",
        ),
        EngineeringControlItem(
            control_id="ctl_crane_hoist_inspection", source="TINKER",
            control_type="Crane/Hoist Inspection",
            rationale="Perform pre-use inspection of all lifting equipment per Tinker AFB Material Handling Equipment protocol.",
        ),
        EngineeringControlItem(
            control_id="ctl_rigging_sling_chain_inspection", source="TINKER",
            control_type="Rigging Sling/Chain Inspection",
            rationale="Inspect rigging slings and chains for rated capacity and integrity before each lift.",
        ),
    ],
    "haz_machine_guards": [
        EngineeringControlItem(
            control_id="ctl_form_493", source="TINKER",
            control_type="LOTO — Form 493",
            rationale="Complete Tinker AFB LOTO Form 493 before removing or bypassing any machine guards for maintenance.",
        ),
    ],
    "haz_pinch_points": [
        EngineeringControlItem(
            control_id="ctl_form_493", source="TINKER",
            control_type="LOTO — Form 493",
            rationale="Complete Tinker AFB LOTO Form 493 to de-energize equipment with pinch-point hazards before maintenance.",
        ),
    ],
    "haz_reaction_pressure_vacuum": [
        EngineeringControlItem(
            control_id="ctl_form_493", source="TINKER",
            control_type="LOTO — Form 493",
            rationale="Complete Tinker AFB LOTO Form 493 before breaking into any pressurized system.",
        ),
        EngineeringControlItem(
            control_id="ctl_depressure_drain", source="TINKER",
            control_type="LOTO — Depressure/Drain",
            rationale="Fully depressurize and drain lines before opening any pressurized or vacuum system.",
        ),
    ],
    # ── Confined Space ──────────────────────────────────────────────────────
    "haz_congestion_tight_spaces": [
        EngineeringControlItem(
            control_id="ctl_gas_test_required_for_all", source="TINKER",
            control_type="Confined Space — Gas Test (required for all)",
            rationale="Perform atmospheric gas test before entering any confined or tight space per Tinker AFB Confined Space requirements.",
        ),
        EngineeringControlItem(
            control_id="ctl_non_permit_required", source="TINKER",
            control_type="Confined Space — Non-Permit Required",
            rationale="Evaluate whether the work area qualifies as Non-Permit Required; document per Tinker AFB procedures.",
        ),
        EngineeringControlItem(
            control_id="ctl_permit_required", source="TINKER",
            control_type="Confined Space — Permit Required",
            rationale="If hazardous atmosphere or engulfment risk exists, obtain a Tinker AFB Permit-Required Confined Space entry permit.",
        ),
    ],
    "haz_ventilation_fumes_mist_dust": [
        EngineeringControlItem(
            control_id="ctl_gas_test_required_for_all", source="TINKER",
            control_type="Confined Space — Gas Test (required for all)",
            rationale="Test atmosphere for O₂ content, flammables, and toxic gases before and during work in poorly ventilated areas.",
        ),
    ],
    # ── Hot Work ────────────────────────────────────────────────────────────
    "haz_fire_explosion": [
        EngineeringControlItem(
            control_id="ctl_standby_fire_watch", source="TINKER",
            control_type="Hot Work — Standby/Fire Watch",
            rationale="Assign a dedicated Fire Watch for all hot work per Tinker AFB Hot Work permit requirements.",
        ),
    ],
    "haz_hazardous_materials_exposure": [
        EngineeringControlItem(
            control_id="ctl_gas_test_required_for_all", source="TINKER",
            control_type="Confined Space — Gas Test (required for all)",
            rationale="Verify atmospheric safety (O₂, LEL, toxics) when handling hazardous materials in confined or semi-enclosed spaces.",
        ),
    ],
    # ── Vehicle Inspection ──────────────────────────────────────────────────
    "haz_fall_from_elevation": [
        EngineeringControlItem(
            control_id="ctl_scissor_lift", source="TINKER",
            control_type="Vehicle Inspection — Scissor Lift",
            rationale="Complete pre-use scissor lift inspection per Tinker AFB Vehicle Inspection requirements before elevated work.",
        ),
        EngineeringControlItem(
            control_id="ctl_boom_lift", source="TINKER",
            control_type="Vehicle Inspection — Boom Lift",
            rationale="Complete pre-use boom lift inspection per Tinker AFB Vehicle Inspection requirements before elevated work.",
        ),
    ],
    "haz_climbing_crawling_bending": [
        EngineeringControlItem(
            control_id="ctl_scissor_lift", source="TINKER",
            control_type="Vehicle Inspection — Scissor Lift",
            rationale="If a scissor lift is used to reach elevated work areas, complete the Tinker AFB pre-use vehicle inspection.",
        ),
        EngineeringControlItem(
            control_id="ctl_boom_lift", source="TINKER",
            control_type="Vehicle Inspection — Boom Lift",
            rationale="If a boom lift is used, complete the Tinker AFB pre-use vehicle inspection before operation.",
        ),
    ],
    "haz_path_of_travel": [
        EngineeringControlItem(
            control_id="ctl_cart_mule_gator", source="TINKER",
            control_type="Vehicle Inspection — Cart/Mule/Gator",
            rationale="Perform pre-use inspection on all carts, mules, and gators in the work area per Tinker AFB Vehicle Inspection requirements.",
        ),
    ],
    "haz_overhead_work_falling_objects": [
        EngineeringControlItem(
            control_id="ctl_crane_hoist_inspection", source="TINKER",
            control_type="Crane/Hoist Inspection",
            rationale="Inspect crane and hoist equipment before overhead lifting to prevent dropped-load incidents.",
        ),
        EngineeringControlItem(
            control_id="ctl_rigging_sling_chain_inspection", source="TINKER",
            control_type="Rigging Sling/Chain Inspection",
            rationale="Inspect all rigging hardware before overhead lifts to verify condition and rated capacity.",
        ),
    ],
}


def _get_all_safety_records(db) -> List[SafetyRecord]:
    """Fetches all safety records from SQLite and constructs Pydantic models."""
    records_query = """
        SELECT sr.*, h.hazard_label, h.hazard_category
        FROM safety_records sr
        JOIN hazards h ON sr.hazard_id = h.hazard_id
    """
    rows = db.execute(records_query).fetchall()

    ppe_query = """
        SELECT srp.record_id, p.ppe_id, p.ppe_label, p.ppe_category
        FROM safety_record_ppe srp
        JOIN ppe p ON srp.ppe_id = p.ppe_id
    """
    ppe_rows = db.execute(ppe_query).fetchall()

    ppe_map: Dict[str, List] = {}
    for r in ppe_rows:
        ppe_map.setdefault(r["record_id"], []).append(
            {"ppe_id": r["ppe_id"], "ppe_label": r["ppe_label"], "ppe_category": r["ppe_category"]}
        )

    safety_records = []
    for row in rows:
        row_dict = dict(row)
        row_dict["ppe_required"] = ppe_map.get(row["record_id"], [])
        safety_records.append(SafetyRecord(**row_dict))

    return safety_records


@router.get("/api/v1/safety-records", response_model=List[SafetyRecord])
def list_safety_records(db=Depends(get_db)):
    """Returns the complete list of safety records in the database."""
    return _get_all_safety_records(db)


@router.get("/api/v1/safety-records/{record_id}", response_model=SafetyRecord)
def get_safety_record(record_id: str, db=Depends(get_db)):
    """Returns a single safety record by its record ID."""
    records = _get_all_safety_records(db)
    for record in records:
        if record.record_id == record_id:
            return record
    raise HTTPException(status_code=404, detail=f"Safety record {record_id} not found")


@router.post("/api/v1/safety-records", response_model=SafetyRecord, status_code=201,
             dependencies=[Depends(require_role("supervisor"))])
def create_safety_record(payload: SafetyRecordCreate, db=Depends(get_db)):
    """Creates a new safety record and associates it with the supplied PPE items."""
    hazard = db.execute(
        "SELECT hazard_id FROM hazards WHERE hazard_id = ?", (payload.hazard_id,)
    ).fetchone()
    if not hazard:
        raise HTTPException(status_code=404, detail=f"Hazard '{payload.hazard_id}' not found")

    for ppe_id in payload.ppe_ids:
        if not db.execute("SELECT 1 FROM ppe WHERE ppe_id = ?", (ppe_id,)).fetchone():
            raise HTTPException(status_code=404, detail=f"PPE item '{ppe_id}' not found")

    record_id = f"SR-{uuid.uuid4().hex[:8].upper()}"

    db.execute(
        """INSERT INTO safety_records
           (record_id, date, location, work_type, hazard_id, exposure_level,
            temperature_f, noise_db, airborne_particles_ppm, supervisor, shift, incident_flag)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            record_id,
            payload.date,
            payload.location,
            payload.work_type,
            payload.hazard_id,
            payload.exposure_level,
            payload.temperature_f,
            payload.noise_db,
            payload.airborne_particles_ppm,
            payload.supervisor,
            payload.shift,
            1 if payload.incident_flag else 0,
        ),
    )

    for ppe_id in payload.ppe_ids:
        db.execute(
            "INSERT INTO safety_record_ppe (record_id, ppe_id) VALUES (?, ?)", (record_id, ppe_id)
        )

    db.commit()
    return get_safety_record(record_id, db)


@router.post("/api/recommend-ppe", response_model=PPERecommendationResponse)
def recommend_ppe(payload: PPERecommendationRequest, db=Depends(get_db)):
    """
    Recommends PPE + engineering controls from SDS-like record patterns and
    severity thresholds derived from historical safety records.
    """
    matched_records = _get_all_safety_records(db)

    if payload.material_id:
        matched_records = [r for r in matched_records if r.hazard_id.lower() == payload.material_id.lower()]

    if payload.process_type:
        process_query = payload.process_type.lower()
        matched_records = [r for r in matched_records if process_query in r.work_type.lower()]

    if not matched_records:
        raise HTTPException(status_code=404, detail="No matching hazard/process records found")

    if payload.severity_level:
        normalized = payload.severity_level.capitalize()
        if normalized not in SEVERITY_RANK:
            raise HTTPException(
                status_code=400, detail="severity_level must be one of: Low, Moderate, High, Severe"
            )
        severity_basis = normalized
    else:
        severity_basis = max(matched_records, key=lambda r: SEVERITY_RANK[r.exposure_level]).exposure_level

    minimum_rank = SEVERITY_RANK[severity_basis]
    severity_filtered = [r for r in matched_records if SEVERITY_RANK[r.exposure_level] >= minimum_rank]

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

    # Add Tinker AFB-specific procedural controls keyed by the exact hazard_id
    for record in severity_filtered:
        for control in TINKER_PROCEDURAL_CONTROLS_BY_HAZARD_ID.get(record.hazard_id, []):
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
        """INSERT INTO ai_assessments (assessment_id, created_at, task_description, response_json)
           VALUES (?, ?, ?, ?)""",
        (assessment_id, created_at, task_description, json.dumps(response.model_dump())),
    )
    db.commit()
    return assessment_id


@router.post("/api/v1/analyze-task", response_model=TaskAnalysisResponse,
             dependencies=[Depends(require_role("analyst"))])
def analyze_task(payload: TaskAnalysisRequest, db=Depends(get_db)):
    """
    Analyzes a natural language description to extract intent and forwards
    the inferred hazards/processes to the standard PPE recommendation engine.
    """
    hazard_id, process_type = analyze_task_description(payload.task_description, db)

    if not hazard_id and not process_type:
        raise HTTPException(
            status_code=400,
            detail="Could not confidently extract hazards or processes from the description. Please be more specific.",
        )

    req = PPERecommendationRequest(
        material_id=hazard_id,
        process_type=process_type,
        severity_level=payload.severity_level,
    )

    try:
        result = recommend_ppe(req, db)
        assessment_id = _persist_ai_assessment(db, payload.task_description, result)
        return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
    except HTTPException:
        if hazard_id and process_type:
            try:
                fallback_req = PPERecommendationRequest(material_id=hazard_id, severity_level=payload.severity_level)
                result = recommend_ppe(fallback_req, db)
                assessment_id = _persist_ai_assessment(db, payload.task_description, result)
                return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
            except HTTPException:
                try:
                    fallback_req = PPERecommendationRequest(
                        process_type=process_type, severity_level=payload.severity_level
                    )
                    result = recommend_ppe(fallback_req, db)
                    assessment_id = _persist_ai_assessment(db, payload.task_description, result)
                    return TaskAnalysisResponse(assessment_id=assessment_id, **result.model_dump())
                except HTTPException:
                    raise
        raise
