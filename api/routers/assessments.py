"""
assessments.py — AI Assessment History Endpoints

Exposes the ai_assessments table so the frontend can display the full history
of AI-generated risk assessment results.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from db.session import get_db
from schemas import AIAssessmentSummary, AIAssessmentDetail, RecommendedPPEItem, EngineeringControlItem

router = APIRouter()


@router.get("/api/v1/ai-assessments", response_model=List[AIAssessmentSummary])
def list_ai_assessments(db=Depends(get_db)):
    """Returns a summary list of all AI assessments, newest first."""
    rows = db.execute(
        """SELECT assessment_id, created_at, task_description, response_json
           FROM ai_assessments
           ORDER BY created_at DESC"""
    ).fetchall()

    results = []
    for row in rows:
        try:
            resp = json.loads(row["response_json"])
            results.append(
                AIAssessmentSummary(
                    assessment_id=row["assessment_id"],
                    created_at=row["created_at"],
                    task_description=row["task_description"],
                    severity_basis=resp.get("severity_basis", "Unknown"),
                    ppe_count=len(resp.get("ppe_recommendations", [])),
                    control_count=len(resp.get("engineering_controls", [])),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return results


@router.get("/api/v1/ai-assessments/{assessment_id}", response_model=AIAssessmentDetail)
def get_ai_assessment(assessment_id: str, db=Depends(get_db)):
    """Returns the full detail of a single AI assessment, including all PPE and controls."""
    row = db.execute(
        """SELECT assessment_id, created_at, task_description, response_json
           FROM ai_assessments
           WHERE assessment_id = ?""",
        (assessment_id,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")

    try:
        resp = json.loads(row["response_json"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored assessment data is malformed")

    return AIAssessmentDetail(
        assessment_id=row["assessment_id"],
        created_at=row["created_at"],
        task_description=row["task_description"],
        criteria=resp.get("criteria", {}),
        severity_basis=resp.get("severity_basis", "Unknown"),
        ppe_recommendations=[RecommendedPPEItem(**p) for p in resp.get("ppe_recommendations", [])],
        engineering_controls=[EngineeringControlItem(**c) for c in resp.get("engineering_controls", [])],
    )
