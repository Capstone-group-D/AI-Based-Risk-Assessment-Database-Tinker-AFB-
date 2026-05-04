from typing import List, Dict, Optional, Literal
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


class TaskAnalysisResponse(PPERecommendationResponse):
    assessment_id: str


class AIFeedbackCreate(BaseModel):
    assessment_id: str
    feedback_type: Literal["thumbs_up", "thumbs_down", "report_inaccuracy"]
    comment: Optional[str] = None

    @model_validator(mode="after")
    def validate_feedback(self):
        if self.feedback_type == "report_inaccuracy" and not (self.comment and self.comment.strip()):
            raise ValueError("comment is required when feedback_type is report_inaccuracy")
        if self.comment is not None and len(self.comment) > 2000:
            raise ValueError("comment must be 2000 characters or fewer")
        return self


class AIFeedbackCreated(BaseModel):
    feedback_id: str
    assessment_id: str
    created_at: str


# ======================
# Waste Management Schemas
# ======================

class WasteCategory(BaseModel):
    waste_category_id: str
    category_name: str
    hazard_class: str
    disposal_method: str
    epa_code: Optional[str] = None


class WasteRecord(BaseModel):
    waste_record_id: str
    date_generated: str
    location: str
    waste_category_id: str
    quantity_kg: float
    quantity_unit: str = "kg"
    generator_name: Optional[str] = None
    process_type: Optional[str] = None
    container_type: Optional[str] = None
    storage_location: Optional[str] = None
    disposal_date: Optional[str] = None
    disposal_method: Optional[str] = None
    recycler_name: Optional[str] = None
    cost_usd: Optional[float] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class RecyclingOpportunity(BaseModel):
    opportunity_id: str
    waste_category_id: str
    opportunity_name: str
    description: str
    recycler_contact: Optional[str] = None
    estimated_value_per_kg: Optional[float] = None
    environmental_impact: Optional[str] = None
    is_active: bool = True
    created_at: str


class PollutionPreventionOpportunity(BaseModel):
    opportunity_id: str
    task_name: str
    task_description: str
    waste_category_id: Optional[str] = None
    prevention_method: str
    expected_reduction_percent: float
    implementation_cost_usd: Optional[float] = None
    payback_period_months: Optional[int] = None
    priority_level: str  # "Low" | "Medium" | "High" | "Critical"
    responsible_party: Optional[str] = None
    status: str = "Identified"  # "Identified" | "Planned" | "Implementing" | "Completed"
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class TaskWasteRelationship(BaseModel):
    task_name: str
    waste_category_id: str
    average_quantity_kg: float
    frequency: str
