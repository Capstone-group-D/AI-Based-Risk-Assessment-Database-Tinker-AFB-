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


app = FastAPI(
    title="PPE Recommendation Engine API",
    description="AI-Based Risk Assessment Database — Tinker AFB",
    version="0.1.0",
)

# CORS — allow the Vite dev server (port 3000) to call this API directly.
# In production this would be restricted to the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
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
        noise_db=85,
        airborne_particles_ppm=12.5,
        supervisor="SSgt Rivera",
        shift="Day",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-001", ppe_label="Chemical-Resistant Gloves", ppe_category="Hand Protection"),
            PPEItem(ppe_id="PPE-002", ppe_label="Safety Goggles", ppe_category="Eye Protection"),
            PPEItem(ppe_id="PPE-003", ppe_label="Respirator (OV cartridge)", ppe_category="Respiratory Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1001",
        date="2024-01-16",
        location="Maintenance Bay 2",
        work_type="Hydraulic Line Maintenance",
        hazard_id="HAZ-002",
        hazard_label="Skydrol Hydraulic Fluid",
        hazard_category="Chemical",
        exposure_level="High",
        temperature_f=72,
        noise_db=70,
        airborne_particles_ppm=3.2,
        supervisor="TSgt Nguyen",
        shift="Day",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-004", ppe_label="Neoprene Gloves", ppe_category="Hand Protection"),
            PPEItem(ppe_id="PPE-005", ppe_label="Face Shield", ppe_category="Eye/Face Protection"),
            PPEItem(ppe_id="PPE-003", ppe_label="Respirator (OV cartridge)", ppe_category="Respiratory Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1002",
        date="2024-01-17",
        location="Battery Shop",
        work_type="Battery Servicing",
        hazard_id="HAZ-003",
        hazard_label="Sulfuric Acid (Battery)",
        hazard_category="Chemical",
        exposure_level="Severe",
        temperature_f=68,
        noise_db=60,
        airborne_particles_ppm=1.8,
        supervisor="MSgt Park",
        shift="Day",
        incident_flag=True,
        ppe_required=[
            PPEItem(ppe_id="PPE-006", ppe_label="Acid-Resistant Gloves", ppe_category="Hand Protection"),
            PPEItem(ppe_id="PPE-005", ppe_label="Face Shield", ppe_category="Eye/Face Protection"),
            PPEItem(ppe_id="PPE-007", ppe_label="Rubber Apron", ppe_category="Body Protection"),
            PPEItem(ppe_id="PPE-008", ppe_label="Acid Respirator", ppe_category="Respiratory Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1003",
        date="2024-01-18",
        location="Paint Booth A",
        work_type="Corrosion Treatment",
        hazard_id="HAZ-004",
        hazard_label="Chromate Primer",
        hazard_category="Chemical",
        exposure_level="Severe",
        temperature_f=75,
        noise_db=65,
        airborne_particles_ppm=8.4,
        supervisor="SSgt Williams",
        shift="Swing",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-001", ppe_label="Nitrile Gloves", ppe_category="Hand Protection"),
            PPEItem(ppe_id="PPE-009", ppe_label="Full-Face Respirator (P100 + OV)", ppe_category="Respiratory Protection"),
            PPEItem(ppe_id="PPE-010", ppe_label="Tyvek Coveralls", ppe_category="Body Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1004",
        date="2024-01-19",
        location="LOX Storage Area",
        work_type="Liquid Oxygen Transfer",
        hazard_id="HAZ-005",
        hazard_label="Liquid Oxygen (LOX)",
        hazard_category="Gas",
        exposure_level="Severe",
        temperature_f=32,
        noise_db=55,
        airborne_particles_ppm=0.0,
        supervisor="Capt Johnson",
        shift="Day",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-011", ppe_label="LOX-Compatible Gloves", ppe_category="Hand Protection"),
            PPEItem(ppe_id="PPE-005", ppe_label="Face Shield", ppe_category="Eye/Face Protection"),
            PPEItem(ppe_id="PPE-012", ppe_label="LOX-Compatible Coveralls", ppe_category="Body Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1005",
        date="2024-01-20",
        location="Confined Space C-7",
        work_type="Nitrogen Purge",
        hazard_id="HAZ-006",
        hazard_label="Nitrogen (High Pressure)",
        hazard_category="Gas",
        exposure_level="High",
        temperature_f=70,
        noise_db=72,
        airborne_particles_ppm=0.0,
        supervisor="TSgt Okafor",
        shift="Night",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-013", ppe_label="SCBA", ppe_category="Respiratory Protection"),
        ],
    ),
    SafetyRecord(
        record_id="REC-1006",
        date="2024-01-21",
        location="Building 412",
        work_type="Lead Paint Abatement",
        hazard_id="HAZ-007",
        hazard_label="Lead-Based Paint Dust",
        hazard_category="Particulate",
        exposure_level="High",
        temperature_f=73,
        noise_db=80,
        airborne_particles_ppm=45.1,
        supervisor="SSgt Chen",
        shift="Day",
        incident_flag=False,
        ppe_required=[
            PPEItem(ppe_id="PPE-014", ppe_label="Half-Face Respirator (P100)", ppe_category="Respiratory Protection"),
            PPEItem(ppe_id="PPE-010", ppe_label="Tyvek Coveralls", ppe_category="Body Protection"),
            PPEItem(ppe_id="PPE-001", ppe_label="Nitrile Gloves", ppe_category="Hand Protection"),
        ],
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
