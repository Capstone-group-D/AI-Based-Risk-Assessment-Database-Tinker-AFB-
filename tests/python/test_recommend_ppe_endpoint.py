import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "api"))
from main import (  # noqa: E402
    recommend_ppe,
    PPERecommendationRequest,
)
from fastapi import HTTPException


def test_recommend_ppe_by_material_id_returns_ppe_and_controls():
    payload = PPERecommendationRequest(material_id="HAZ-003")
    response = recommend_ppe(payload)

    assert response.severity_basis == "Severe"
    assert len(response.ppe_recommendations) >= 1
    assert len(response.engineering_controls) >= 1
    assert any(item.ppe_type == "Acid-Resistant Gloves" for item in response.ppe_recommendations)


def test_recommend_ppe_by_process_and_threshold_severity_filters_records():
    payload = PPERecommendationRequest(process_type="maintenance", severity_level="High")
    response = recommend_ppe(payload)

    categories = {item.ppe_category for item in response.ppe_recommendations}
    assert "Respiratory Protection" in categories


def test_recommend_ppe_rejects_invalid_severity_level():
    payload = PPERecommendationRequest(process_type="Fueling", severity_level="Critical")
    try:
        recommend_ppe(payload)
        assert False, "Expected HTTPException for invalid severity"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_recommend_ppe_raises_not_found_when_no_match():
    payload = PPERecommendationRequest(material_id="HAZ-999")
    try:
        recommend_ppe(payload)
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