import sys
from pathlib import Path
import pytest
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "api"))
from schemas import (
    PPERecommendationRequest,
    SafetyRecord,
    PPEItem
)
from routers.safety_records import recommend_ppe
from fastapi import HTTPException

# Recovered from previous in-memory DB for tests
MOCK_SAFETY_RECORDS_DB = [
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

@pytest.fixture(autouse=True)
def mock_get_all_records():
    with patch("routers.safety_records._get_all_safety_records") as mock_get:
        mock_get.return_value = MOCK_SAFETY_RECORDS_DB
        yield mock_get

def test_recommend_ppe_by_material_id_returns_ppe_and_controls():
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)


    assert response.severity_basis == "Severe"
    assert len(response.ppe_recommendations) >= 1
    assert len(response.engineering_controls) >= 1
    assert any(item.ppe_type == "Full-Face Respirator (P100)" for item in response.ppe_recommendations)
    assert any(item.ppe_category == "Respiratory Protection" for item in response.ppe_recommendations)
    assert any(item.ppe_category == "Body Protection" for item in response.ppe_recommendations)
    assert any(item.ppe_category == "Hand Protection" for item in response.ppe_recommendations)


def test_recommend_ppe_by_process_type_fueling_operations():
    """Test PPE recommendations for fueling operations."""
    payload = PPERecommendationRequest(process_type="Fueling")
    response = recommend_ppe(payload, db=None)

    assert response.severity_basis == "High"
    assert response.criteria["process_type"] == "Fueling"
    assert len(response.ppe_recommendations) == 0  # Current data doesn't have PPE for this record
    # But should have engineering controls for Chemical category
    assert len(response.engineering_controls) >= 1
    assert any(control.control_type == "Local Exhaust Ventilation" for control in response.engineering_controls)


def test_recommend_ppe_with_explicit_severity_filtering():
    """Test that explicit severity level filters records appropriately."""
    payload = PPERecommendationRequest(process_type="Structural", severity_level="Severe")
    response = recommend_ppe(payload, db=None)

    assert response.severity_basis == "Severe"
    assert len(response.ppe_recommendations) >= 3  # Should include all PPE from the asbestos record
    ppe_types = {item.ppe_type for item in response.ppe_recommendations}
    assert "Full-Face Respirator (P100)" in ppe_types
    assert "Disposable Coveralls (Type 5/6)" in ppe_types
    assert "Nitrile Gloves" in ppe_types


def test_recommend_ppe_chemical_hazard_engineering_controls():
    """Test that chemical hazards return appropriate engineering controls."""
    payload = PPERecommendationRequest(process_type="Fueling")
    response = recommend_ppe(payload, db=None)

    controls = {control.control_type for control in response.engineering_controls}
    assert "Local Exhaust Ventilation" in controls
    assert "Closed Transfer / Secondary Containment" in controls


def test_recommend_ppe_particulate_hazard_engineering_controls():
    """Test that particulate hazards return appropriate engineering controls."""
    payload = PPERecommendationRequest(material_id="HAZ-008")  # Asbestos - particulate
    response = recommend_ppe(payload, db=None)

    categories = {item.ppe_category for item in response.ppe_recommendations}
    assert "Respiratory Protection" in categories


def test_recommend_ppe_rejects_invalid_severity_level():
    payload = PPERecommendationRequest(process_type="Fueling", severity_level="Critical")
    try:
        recommend_ppe(payload, db=None)
        assert False, "Expected HTTPException for invalid severity"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_recommend_ppe_raises_not_found_when_no_match():
    payload = PPERecommendationRequest(material_id="HAZ-999")
    try:
        recommend_ppe(payload, db=None)
        assert False, "Expected HTTPException for unmatched filters"
    except HTTPException as exc:
        assert exc.status_code == 404


def test_recommend_ppe_requires_selector():
    from pydantic import ValidationError

    try:
        PPERecommendationRequest()
        assert False, "Expected ValidationError when neither selector is provided"
    except ValidationError:
        assert True


# ─── Additional Happy Path Tests ──────────────────────────────────────────────

def test_recommend_ppe_chemical_hazard_fueling_operations():
    """Test PPE recommendations for chemical hazards in fueling operations."""
    payload = PPERecommendationRequest(process_type="Fueling")
    response = recommend_ppe(payload, db=None)

    assert response.severity_basis == "High"
    assert response.criteria["process_type"] == "Fueling"
    # Current data shows no PPE for this record, but should have engineering controls
    assert len(response.engineering_controls) >= 1
    assert any(control.control_type == "Local Exhaust Ventilation" for control in response.engineering_controls)


def test_recommend_ppe_particulate_hazard_asbestos():
    """Test PPE recommendations for particulate hazards like asbestos."""
    payload = PPERecommendationRequest(material_id="HAZ-008")  # Asbestos
    response = recommend_ppe(payload, db=None)

    assert response.severity_basis == "Severe"
    assert len(response.ppe_recommendations) >= 3  # Should have multiple PPE items
    ppe_categories = {item.ppe_category for item in response.ppe_recommendations}
    assert "Respiratory Protection" in ppe_categories
    assert "Body Protection" in ppe_categories
    assert "Hand Protection" in ppe_categories




# ─── Additional Edge Case Tests ───────────────────────────────────────────────

def test_recommend_ppe_unknown_process_type():
    """Test behavior with unknown process type."""
    payload = PPERecommendationRequest(process_type="unknown_process")
    try:
        recommend_ppe(payload, db=None)
        assert False, "Expected HTTPException for unknown process type"
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "No matching hazard/process records found" in exc.detail


def test_recommend_ppe_empty_material_id():
    """Test behavior with empty material_id string."""
    from pydantic import ValidationError
    try:
        PPERecommendationRequest(material_id="")
        assert False, "Expected ValidationError for empty material_id"
    except ValidationError:
        assert True


def test_recommend_ppe_case_insensitive_material_id():
    """Test that material_id matching is case insensitive."""
    payload = PPERecommendationRequest(material_id="haz-008")  # lowercase
    response = recommend_ppe(payload, db=None)
    assert response.severity_basis == "Severe"


def test_recommend_ppe_case_insensitive_process_type():
    """Test that process_type matching is case insensitive."""
    payload = PPERecommendationRequest(process_type="FUELING")  # uppercase
    response = recommend_ppe(payload, db=None)
    assert response.severity_basis == "High"


def test_recommend_ppe_partial_match_multiple_words():
    """Test partial matching with multi-word process types."""
    payload = PPERecommendationRequest(process_type="structural inspection")  # full match
    response = recommend_ppe(payload, db=None)
    assert response.severity_basis == "Severe"

    payload = PPERecommendationRequest(process_type="inspection")  # partial match
    response = recommend_ppe(payload, db=None)
    assert response.severity_basis == "Severe"


# ─── Calculation Function Tests ───────────────────────────────────────────────

def test_severity_rank_mapping():
    """Test that severity ranking is correctly defined."""
    from routers.safety_records import SEVERITY_RANK
    assert SEVERITY_RANK["Low"] == 1
    assert SEVERITY_RANK["Moderate"] == 2
    assert SEVERITY_RANK["High"] == 3
    assert SEVERITY_RANK["Severe"] == 4
    assert len(SEVERITY_RANK) == 4


def test_engineering_control_rules_structure():
    """Test that engineering control rules are properly structured."""
    from routers.safety_records import ENGINEERING_CONTROL_RULES
    assert "Chemical" in ENGINEERING_CONTROL_RULES
    assert "Gas" in ENGINEERING_CONTROL_RULES
    assert "Particulate" in ENGINEERING_CONTROL_RULES

    # Test Chemical controls
    chemical_controls = ENGINEERING_CONTROL_RULES["Chemical"]
    assert len(chemical_controls) == 2
    control_types = {control.control_type for control in chemical_controls}
    assert "Local Exhaust Ventilation" in control_types
    assert "Closed Transfer / Secondary Containment" in control_types

    # Test Particulate controls
    particulate_controls = ENGINEERING_CONTROL_RULES["Particulate"]
    assert len(particulate_controls) == 2
    control_types = {control.control_type for control in particulate_controls}
    assert "HEPA-Filtered Negative Pressure Enclosure" in control_types
    assert "Wet Methods / Dust Suppression" in control_types


def test_severity_rank_ordering():
    """Test that severity ranking correctly orders severities."""
    from routers.safety_records import SEVERITY_RANK
    assert SEVERITY_RANK["Low"] < SEVERITY_RANK["Moderate"]
    assert SEVERITY_RANK["Moderate"] < SEVERITY_RANK["High"]
    assert SEVERITY_RANK["High"] < SEVERITY_RANK["Severe"]


def test_max_severity_calculation_logic():
    """Test the max severity calculation from a list of records."""
    from routers.safety_records import SEVERITY_RANK
    # Simulate the logic
    records = [
        type('MockRecord', (), {'exposure_level': 'Low'})(),
        type('MockRecord', (), {'exposure_level': 'High'})(),
        type('MockRecord', (), {'exposure_level': 'Moderate'})(),
    ]
    max_record = max(records, key=lambda row: SEVERITY_RANK[row.exposure_level])
    assert max_record.exposure_level == "High"


def test_ppe_deduplication():
    """Test that duplicate PPE items are properly deduplicated."""
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)

    ppe_ids = [item.ppe_id for item in response.ppe_recommendations]
    assert len(ppe_ids) == len(set(ppe_ids))  # No duplicates


def test_engineering_controls_deduplication():
    """Test that duplicate engineering controls are properly deduplicated."""
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)

    control_types = [control.control_type for control in response.engineering_controls]
    assert len(control_types) == len(set(control_types))  # No duplicates


# ─── Boundary and Stress Tests ────────────────────────────────────────────────

def test_recommend_ppe_very_long_material_id():
    """Test behavior with very long material_id."""
    long_id = "HAZ-" + "0" * 1000  # Very long ID
    payload = PPERecommendationRequest(material_id=long_id)
    try:
        recommend_ppe(payload, db=None)
        assert False, "Expected HTTPException for non-existent material_id"
    except HTTPException as exc:
        assert exc.status_code == 404


def test_recommend_ppe_special_characters_process_type():
    """Test process type with special characters."""
    payload = PPERecommendationRequest(process_type="test-process_type")
    try:
        recommend_ppe(payload, db=None)
        assert False, "Expected HTTPException for unknown process type"
    except HTTPException as exc:
        assert exc.status_code == 404


# ─── Integration and System Tests ─────────────────────────────────────────────

def test_recommend_ppe_full_response_validation():
    """Test complete response validation for all fields and types."""
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)

    # Validate all fields are present and correctly typed
    assert isinstance(response.criteria, dict)
    assert isinstance(response.severity_basis, str)
    assert isinstance(response.ppe_recommendations, list)
    assert isinstance(response.engineering_controls, list)

    # Validate PPE items structure
    for ppe in response.ppe_recommendations:
        assert hasattr(ppe, 'ppe_id')
        assert hasattr(ppe, 'ppe_type')
        assert hasattr(ppe, 'ppe_category')
        assert hasattr(ppe, 'rationale')
        assert isinstance(ppe.ppe_id, str)
        assert isinstance(ppe.ppe_type, str)
        assert isinstance(ppe.ppe_category, str)
        assert isinstance(ppe.rationale, str)

    # Validate engineering controls structure
    for control in response.engineering_controls:
        assert hasattr(control, 'control_type')
        assert hasattr(control, 'rationale')
        assert isinstance(control.control_type, str)
        assert isinstance(control.rationale, str)


def test_recommend_ppe_rationale_content_accuracy():
    """Test that PPE rationales contain accurate and relevant information."""
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)

    for ppe in response.ppe_recommendations:
        rationale = ppe.rationale.lower()
        assert "asbestos" in rationale
        assert "structural" in rationale
        assert "severe" in rationale
        assert "historical" in rationale or "sds" in rationale


def test_recommend_ppe_engineering_control_rationale():
    """Test that engineering control rationales are appropriate."""
    payload = PPERecommendationRequest(material_id="HAZ-008")
    response = recommend_ppe(payload, db=None)

    for control in response.engineering_controls:
        rationale = control.rationale.lower()
        if "hepa" in control.control_type.lower():
            assert "particulate" in rationale or "fine" in rationale
        elif "wet methods" in control.control_type.lower():
            assert "dust" in rationale or "particle" in rationale