"""
main.py — FastAPI Backend for AI-Based Risk Assessment Database

Tinker AFB PPE Recommendation Engine — Sprint 2 API

Endpoints:
  GET /api/v1/health            — Health check / connectivity probe
  GET /api/v1/hazmat            — List all hazardous materials
  GET /api/v1/hazmat/{id}       — Retrieve a single hazardous material by ID

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
    name: str
    category: str
    rationale: str


class HazardousMaterial(BaseModel):
    id: int
    code: str
    name: str
    category: str
    hazard_class: str
    exposure_routes: List[str]
    severity: str        # "Low" | "Medium" | "High" | "Critical"
    ppe_required: List[PPEItem]


# ─── In-Memory Hazmat Database ───────────────────────────────────────────────────
# Temporary stub data for frontend-backend integration testing.
# Replace with PostgreSQL queries from db when the database layer is ready.

HAZMAT_DB: List[HazardousMaterial] = [
    HazardousMaterial(
        id=1,
        code="CHEM-001",
        name="JP-8 Jet Fuel",
        category="Chemical",
        hazard_class="Flammable Liquid",
        exposure_routes=["inhalation", "skin contact", "ingestion"],
        severity="High",
        ppe_required=[
            PPEItem(name="Chemical-Resistant Gloves", category="Hand Protection",
                    rationale="Prevents skin absorption of hydrocarbons"),
            PPEItem(name="Safety Goggles", category="Eye Protection",
                    rationale="Protects against splash and vapor mist"),
            PPEItem(name="Respirator (OV cartridge)", category="Respiratory Protection",
                    rationale="Filters hydrocarbon vapors above the PEL"),
            PPEItem(name="Chemical-Resistant Apron", category="Body Protection",
                    rationale="Reduces skin exposure during fueling operations"),
        ],
    ),
    HazardousMaterial(
        id=2,
        code="CHEM-002",
        name="Skydrol Hydraulic Fluid",
        category="Chemical",
        hazard_class="Corrosive Liquid",
        exposure_routes=["skin contact", "eye contact", "inhalation"],
        severity="High",
        ppe_required=[
            PPEItem(name="Neoprene Gloves", category="Hand Protection",
                    rationale="Skydrol penetrates latex — neoprene required"),
            PPEItem(name="Face Shield", category="Eye/Face Protection",
                    rationale="Corrosive; splash risk during pressure line work"),
            PPEItem(name="Respirator (OV cartridge)", category="Respiratory Protection",
                    rationale="Mist irritates the respiratory tract"),
            PPEItem(name="Tyvek Coveralls", category="Body Protection",
                    rationale="Full skin coverage for hydraulic line maintenance"),
        ],
    ),
    HazardousMaterial(
        id=3,
        code="CHEM-003",
        name="Sulfuric Acid (Battery)",
        category="Chemical",
        hazard_class="Corrosive Acid",
        exposure_routes=["skin contact", "eye contact", "inhalation"],
        severity="Critical",
        ppe_required=[
            PPEItem(name="Acid-Resistant Gloves", category="Hand Protection",
                    rationale="Prevents severe chemical burns on contact"),
            PPEItem(name="Face Shield", category="Eye/Face Protection",
                    rationale="Acid splash causes permanent eye damage"),
            PPEItem(name="Rubber Apron", category="Body Protection",
                    rationale="Full torso protection during battery servicing"),
            PPEItem(name="Acid Respirator", category="Respiratory Protection",
                    rationale="Acid mist exposure causes respiratory damage"),
        ],
    ),
    HazardousMaterial(
        id=4,
        code="CHEM-004",
        name="Methyl Ethyl Ketone (MEK)",
        category="Chemical",
        hazard_class="Flammable Liquid",
        exposure_routes=["inhalation", "skin contact", "ingestion"],
        severity="Medium",
        ppe_required=[
            PPEItem(name="Nitrile Gloves", category="Hand Protection",
                    rationale="Prevents skin absorption and contact dermatitis"),
            PPEItem(name="Safety Goggles", category="Eye Protection",
                    rationale="Vapor and splash cause eye irritation"),
            PPEItem(name="Respirator (OV cartridge)", category="Respiratory Protection",
                    rationale="CNS depressant at high vapor concentrations"),
        ],
    ),
    HazardousMaterial(
        id=5,
        code="CHEM-005",
        name="Chromate Primer (Corrosion Inhibiting)",
        category="Chemical",
        hazard_class="Carcinogen / Toxic",
        exposure_routes=["inhalation", "skin contact"],
        severity="Critical",
        ppe_required=[
            PPEItem(name="Nitrile Gloves", category="Hand Protection",
                    rationale="Hexavalent chromium is a confirmed carcinogen"),
            PPEItem(name="Full-Face Respirator (P100 + OV)", category="Respiratory Protection",
                    rationale="Airborne chromate particles are carcinogenic"),
            PPEItem(name="Tyvek Coveralls", category="Body Protection",
                    rationale="Prevents chromate dust deposition on skin and clothing"),
            PPEItem(name="Safety Goggles", category="Eye Protection",
                    rationale="Splash and mist protection during spray application"),
        ],
    ),
    HazardousMaterial(
        id=6,
        code="GAS-001",
        name="Liquid Oxygen (LOX)",
        category="Gas",
        hazard_class="Oxidizer / Cryogenic",
        exposure_routes=["skin contact (cryogenic burn)", "inhalation (O2 enrichment)"],
        severity="Critical",
        ppe_required=[
            PPEItem(name="LOX-Compatible Gloves (leather/cryogenic)", category="Hand Protection",
                    rationale="Cryogenic contact causes instant frostbite"),
            PPEItem(name="Face Shield", category="Eye/Face Protection",
                    rationale="Cryogenic splash and oxygen vapor pressure protection"),
            PPEItem(name="LOX-Compatible Coveralls (no synthetics)", category="Body Protection",
                    rationale="Oxygen-saturated synthetic clothing ignites spontaneously"),
        ],
    ),
    HazardousMaterial(
        id=7,
        code="GAS-002",
        name="Nitrogen (High Pressure)",
        category="Gas",
        hazard_class="Asphyxiant",
        exposure_routes=["inhalation (confined space displacement)"],
        severity="High",
        ppe_required=[
            PPEItem(name="SCBA (Self-Contained Breathing Apparatus)", category="Respiratory Protection",
                    rationale="Displaces oxygen — immediately dangerous to life in confined spaces"),
            PPEItem(name="Confined Space Entry Permit", category="Administrative Control",
                    rationale="Required per OSHA 29 CFR 1910.146 for nitrogen-pressurized spaces"),
        ],
    ),
    HazardousMaterial(
        id=8,
        code="PHYS-001",
        name="Lead-Based Paint Dust",
        category="Particulate",
        hazard_class="Heavy Metal / Toxic",
        exposure_routes=["inhalation", "ingestion"],
        severity="High",
        ppe_required=[
            PPEItem(name="Half-Face Respirator (P100)", category="Respiratory Protection",
                    rationale="HEPA filtration required for lead dust — PEL 50 µg/m³"),
            PPEItem(name="Tyvek Coveralls", category="Body Protection",
                    rationale="Prevents secondary contamination via clothing"),
            PPEItem(name="Nitrile Gloves", category="Hand Protection",
                    rationale="Prevents hand-to-mouth ingestion pathway"),
            PPEItem(name="Safety Goggles", category="Eye Protection",
                    rationale="Prevents ingestion via tear duct and eye irritation"),
        ],
    ),
    HazardousMaterial(
        id=9,
        code="PHYS-002",
        name="Asbestos Containing Material (ACM)",
        category="Particulate",
        hazard_class="Carcinogen",
        exposure_routes=["inhalation"],
        severity="Critical",
        ppe_required=[
            PPEItem(name="Full-Face Respirator (P100)", category="Respiratory Protection",
                    rationale="Asbestos fibers cause mesothelioma — HEPA mandatory"),
            PPEItem(name="Disposable Coveralls (Type 5/6)", category="Body Protection",
                    rationale="Single-use to prevent fiber transport outside work area"),
            PPEItem(name="Nitrile Gloves", category="Hand Protection",
                    rationale="Prevents fiber transfer to other surfaces and personnel"),
        ],
    ),
    HazardousMaterial(
        id=10,
        code="ELEC-001",
        name="Hydraulic Actuator (High Pressure)",
        category="Physical",
        hazard_class="High-Pressure Fluid / Injection Hazard",
        exposure_routes=["skin injection", "blunt impact"],
        severity="Critical",
        ppe_required=[
            PPEItem(name="Face Shield", category="Eye/Face Protection",
                    rationale="High-pressure fluid injection can penetrate skin at distance"),
            PPEItem(name="Leather Work Gloves", category="Hand Protection",
                    rationale="Impact and fluid jet protection during line removal"),
            PPEItem(name="Safety Boots (steel-toe)", category="Foot Protection",
                    rationale="Protection against dropped actuator components"),
        ],
    ),
]


# ─── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint — used by the frontend header to probe connectivity."""
    return {"status": "ok", "message": "API online", "version": "0.1.0"}


@app.get("/api/v1/hazmat", response_model=List[HazardousMaterial])
def list_hazmat():
    """Returns the complete list of hazardous materials in the database."""
    return HAZMAT_DB


@app.get("/api/v1/hazmat/{hazmat_id}", response_model=HazardousMaterial)
def get_hazmat(hazmat_id: int):
    """Returns a single hazardous material by its numeric ID."""
    for item in HAZMAT_DB:
        if item.id == hazmat_id:
            return item
    raise HTTPException(status_code=404, detail=f"Hazardous material {hazmat_id} not found")
