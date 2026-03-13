"""
main.py — FastAPI Backend for AI-Based Risk Assessment Database

Tinker AFB PPE Recommendation Engine — Sprint 2 API

Endpoints:
  GET /api/v1/health                    — Health check / connectivity probe
  GET /api/v1/safety-records            — List all safety records
  GET /api/v1/safety-records/{id}       — Retrieve a single safety record by ID

Run with:
  uvicorn main:app --reload --port 8000
  (from the /api directory, or `uvicorn api.main:app` from the project root)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from typing import Dict, List, Optional
from pydantic import BaseModel, model_validator

from core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Risk Assessment Database — Tinker AFB",
    version=settings.VERSION,
)

# CORS — allow the Vite dev server (port 3000) to call this API directly.
# In production this would be restricted to the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Data Models ────────────────────────────────────────────────────────────────

class PPEItem(BaseModel):
    ppe_id: str
    ppe_label: str
    ppe_category: str


class SafetyRecord(BaseModel):
    record_id: str
    date: str
    location: str
    work_type: str
    hazard_id: str
    hazard_label: str
    hazard_category: str
    exposure_level: str       # "Low" | "Moderate" | "High" | "Severe"
    temperature_f: int
    noise_db: int
    airborne_particles_ppm: float
    supervisor: str
    shift: str                # "Day" | "Swing" | "Night"
    incident_flag: bool
    ppe_required: List[PPEItem]


class PPERecommendationRequest(BaseModel):
    material_id: Optional[str] = None
    process_type: Optional[str] = None
    severity_level: Optional[str] = None

    @model_validator(mode="after")
    def validate_selector(self):
        if not self.material_id and not self.process_type:
            raise ValueError("Either material_id or process_type is required")
        return self


class RecommendedPPEItem(BaseModel):
    ppe_id: str
    ppe_type: str
    ppe_category: str
    rationale: str


class EngineeringControlItem(BaseModel):
    control_type: str
    rationale: str


class PPERecommendationResponse(BaseModel):
    criteria: Dict[str, Optional[str]]
    severity_basis: str
    ppe_recommendations: List[RecommendedPPEItem]
    engineering_controls: List[EngineeringControlItem]


# ─── In-Memory Safety Records Database ──────────────────────────────────────────
# Temporary stub data for frontend-backend integration testing.
# Replace with PostgreSQL queries when the database layer is ready (see db/schema.sql).
#
# Relevant tables and columns to query:
#   hazards           → hazard_id, hazard_label, hazard_category
#   ppe               → ppe_id, ppe_label, ppe_category
#   safety_records    → record_id, date, location, work_type, hazard_id, exposure_level,
#                       temperature_f, noise_db, airborne_particles_ppm, supervisor, shift,
#                       incident_flag
#   safety_record_ppe → record_id, ppe_id  (join: which PPE belongs to each record)
#
# Seed data lives in db/seed_data.sql (120 safety records, REC-1000 through REC-1119).

SAFETY_RECORDS_DB: List[SafetyRecord] = [
    SafetyRecord(
        record_id="REC-1000",
        date="2024-01-15",
        location="Hangar 5",
        work_type="Fueling Operations",
        hazard_id="HAZ-001",
        hazard_label="JP-8 Jet Fuel",
        hazard_category="Chemical",
        exposure_level="High",
        temperature_f=78,
    ),
    SafetyRecord(
        record_id="REC-1007",
        date="2024-01-22",
        location="Hangar 3",
        work_type="Structural Inspection",
        hazard_id="HAZ-008",
        hazard_label="Asbestos Containing Material",
        hazard_category="Particulate",
        exposure_level="Severe",
        temperature_f=71,
        noise_db=68,
        airborne_particles_ppm=22.7,
        supervisor="MSgt Torres",
        shift="Day",
        incident_flag=True,
        ppe_required=[
            PPEItem(ppe_id="PPE-015", ppe_label="Full-Face Respirator (P100)", ppe_category="Respiratory Protection"),
            PPEItem(ppe_id="PPE-016", ppe_label="Disposable Coveralls (Type 5/6)", ppe_category="Body Protection"),
            PPEItem(ppe_id="PPE-001", ppe_label="Nitrile Gloves", ppe_category="Hand Protection"),
        ],
    ),
]

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


# ─── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint — used by the frontend header to probe connectivity."""
    return {"status": "ok", "message": "API online", "version": "0.1.0"}


@app.get("/api/v1/safety-records", response_model=List[SafetyRecord])
def list_safety_records():
    """Returns the complete list of safety records in the database."""
    return SAFETY_RECORDS_DB


@app.get("/api/v1/safety-records/{record_id}", response_model=SafetyRecord)
def get_safety_record(record_id: str):
    """Returns a single safety record by its record ID."""
    for record in SAFETY_RECORDS_DB:
        if record.record_id == record_id:
            return record
    raise HTTPException(status_code=404, detail=f"Safety record {record_id} not found")


@app.post("/api/recommend-ppe", response_model=PPERecommendationResponse)
def recommend_ppe(payload: PPERecommendationRequest):
    """
    Recommends PPE + engineering controls from SDS-like record patterns and
    severity thresholds derived from historical safety records.
    """
    matched_records = SAFETY_RECORDS_DB

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