import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "api"))

from schemas import AIFeedbackCreate, AIFeedbackCreated
from routers.feedback import submit_ai_feedback
from fastapi import HTTPException


@pytest.fixture
def mock_db_with_assessment():
    """Mock DB connection where the assessment exists."""
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = {"ok": 1}
    return db


@pytest.fixture
def mock_db_no_assessment():
    """Mock DB connection where the assessment does NOT exist."""
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = None
    return db


def test_thumbs_up_success(mock_db_with_assessment):
    payload = AIFeedbackCreate(
        assessment_id="test-uuid-123",
        feedback_type="thumbs_up",
    )

    result = submit_ai_feedback(payload, db=mock_db_with_assessment)

    assert isinstance(result, AIFeedbackCreated)
    assert result.assessment_id == "test-uuid-123"
    assert result.feedback_id is not None
    assert result.created_at is not None
    mock_db_with_assessment.commit.assert_called()


def test_thumbs_down_success(mock_db_with_assessment):
    payload = AIFeedbackCreate(
        assessment_id="test-uuid-456",
        feedback_type="thumbs_down",
    )

    result = submit_ai_feedback(payload, db=mock_db_with_assessment)

    assert isinstance(result, AIFeedbackCreated)
    assert result.assessment_id == "test-uuid-456"
    mock_db_with_assessment.commit.assert_called()


def test_report_inaccuracy_success(mock_db_with_assessment):
    payload = AIFeedbackCreate(
        assessment_id="test-uuid-789",
        feedback_type="report_inaccuracy",
        comment="Missing hearing protection for grinding task.",
    )

    result = submit_ai_feedback(payload, db=mock_db_with_assessment)

    assert isinstance(result, AIFeedbackCreated)
    assert result.assessment_id == "test-uuid-789"
    mock_db_with_assessment.commit.assert_called()


def test_report_inaccuracy_requires_comment():
    """Report inaccuracy must include a non-empty comment."""
    with pytest.raises(ValueError, match="comment is required"):
        AIFeedbackCreate(
            assessment_id="test-uuid",
            feedback_type="report_inaccuracy",
            comment=None,
        )

    with pytest.raises(ValueError, match="comment is required"):
        AIFeedbackCreate(
            assessment_id="test-uuid",
            feedback_type="report_inaccuracy",
            comment="   ",
        )


def test_comment_max_length():
    """Comment must be 2000 characters or fewer."""
    long_comment = "x" * 2001
    with pytest.raises(ValueError, match="2000 characters"):
        AIFeedbackCreate(
            assessment_id="test-uuid",
            feedback_type="report_inaccuracy",
            comment=long_comment,
        )


def test_invalid_assessment_id_returns_404(mock_db_no_assessment):
    payload = AIFeedbackCreate(
        assessment_id="nonexistent-uuid",
        feedback_type="thumbs_up",
    )

    with pytest.raises(HTTPException) as exc_info:
        submit_ai_feedback(payload, db=mock_db_no_assessment)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_invalid_feedback_type():
    """Feedback type must be one of the allowed values."""
    with pytest.raises(ValueError):
        AIFeedbackCreate(
            assessment_id="test-uuid",
            feedback_type="invalid_type",
        )
