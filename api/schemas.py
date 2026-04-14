from typing import List, Dict, Optional
from pydantic import BaseModel, model_validator


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
    temperature_f: Optional[int] = None
    noise_db: Optional[int] = None
    airborne_particles_ppm: Optional[float] = None
    supervisor: Optional[str] = None
    shift: Optional[str] = None                # "Day" | "Swing" | "Night"
    incident_flag: Optional[bool] = False
    ppe_required: List[PPEItem] = []


class PPERecommendationRequest(BaseModel):
    material_id: Optional[str] = None
    process_type: Optional[str] = None
    severity_level: Optional[str] = None

    @model_validator(mode="after")
    def validate_selector(self):
        if not self.material_id and not self.process_type:
            raise ValueError("Either material_id or process_type is required")
        return self

class TaskAnalysisRequest(BaseModel):
    task_description: str
    severity_level: Optional[str] = "Moderate"

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
