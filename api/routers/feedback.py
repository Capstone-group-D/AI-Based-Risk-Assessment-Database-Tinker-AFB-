from fastapi import APIRouter, Depends, HTTPException
import uuid
from datetime import datetime

from db.session import get_db
from schemas import AIFeedbackCreate, AIFeedbackCreated


router = APIRouter()


@router.post("/api/v1/ai-feedback", response_model=AIFeedbackCreated)
def submit_ai_feedback(payload: AIFeedbackCreate, db=Depends(get_db)):
    exists = db.execute(
        "SELECT 1 AS ok FROM ai_assessments WHERE assessment_id = ? LIMIT 1",
        (payload.assessment_id,),
    ).fetchone()

    if not exists:
        raise HTTPException(status_code=404, detail="assessment_id not found")

    feedback_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    db.execute(
        """
        INSERT INTO ai_feedback (feedback_id, created_at, assessment_id, feedback_type, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            feedback_id,
            created_at,
            payload.assessment_id,
            payload.feedback_type,
            payload.comment,
        ),
    )
    db.commit()

    return AIFeedbackCreated(
        feedback_id=feedback_id,
        assessment_id=payload.assessment_id,
        created_at=created_at,
    )

