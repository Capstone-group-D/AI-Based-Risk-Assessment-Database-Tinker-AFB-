"""
assessments.py — AI Assessment History Endpoints

Exposes the ai_assessments table so the frontend can display the full history
of AI-generated risk assessment results.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import List
import csv
import io

from db.session import get_db
from schemas import AIAssessmentSummary, AIAssessmentDetail, RecommendedPPEItem, EngineeringControlItem

router = APIRouter()


@router.get("/api/v1/ai-assessments/export")
def export_assessments_csv(db=Depends(get_db)):
    """Returns all AI assessments as a downloadable CSV summary."""
    rows = db.execute(
        """SELECT assessment_id, created_at, task_description, response_json
           FROM ai_assessments ORDER BY created_at DESC"""
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Assessment ID", "Date", "Task Description", "Severity", "PPE Count", "Controls Count"])

    for row in rows:
        try:
            resp = json.loads(row["response_json"])
            writer.writerow([
                row["assessment_id"],
                row["created_at"],
                row["task_description"],
                resp.get("severity_basis", ""),
                len(resp.get("ppe_recommendations", [])),
                len(resp.get("engineering_controls", [])),
            ])
        except (json.JSONDecodeError, KeyError):
            continue

    output.seek(0)
    filename = f"tinker_assessments_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@router.get("/api/v1/ai-assessments/{assessment_id}/report", response_class=HTMLResponse)
def get_assessment_report(assessment_id: str, db=Depends(get_db)):
    """
    Returns a print-ready HTML page for a single assessment.
    Open in a browser and use Ctrl/Cmd+P → Save as PDF.
    """
    row = db.execute(
        """SELECT assessment_id, created_at, task_description, response_json
           FROM ai_assessments WHERE assessment_id = ?""",
        (assessment_id,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")

    try:
        resp = json.loads(row["response_json"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored assessment data is malformed")

    ppe_items = resp.get("ppe_recommendations", [])
    controls = resp.get("engineering_controls", [])
    criteria = resp.get("criteria", {})
    severity = resp.get("severity_basis", "Unknown")
    created = row["created_at"]

    # Build PPE rows
    ppe_rows = "".join(
        f"<tr><td>{p.get('ppe_label','')}</td><td>{p.get('ppe_category','')}</td>"
        f"<td>{p.get('rationale','')}</td></tr>"
        for p in ppe_items
    )

    # Build controls rows
    ctrl_rows = "".join(
        f"<tr><td>{c.get('control_type','')}"
        + (' <span class=\"tinker-tag\">TINKER AFB FORM</span>' if c.get('source') == 'TINKER' else '')
        + f"</td><td>{c.get('rationale','')}</td></tr>"
        for c in controls
    )

    # Build criteria rows
    criteria_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in criteria.items()
    )

    SEVERITY_COLOR = {
        "Low": "#2e7d32", "Moderate": "#e65100",
        "High": "#c62828", "Severe": "#b71c1c",
    }
    sev_color = SEVERITY_COLOR.get(severity, "#333")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Risk Assessment Report — {assessment_id}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 11pt; color: #222; padding: 30px 40px; }}
  header {{ border-bottom: 3px solid #b71c1c; padding-bottom: 12px; margin-bottom: 20px; }}
  header h1 {{ font-size: 18pt; color: #b71c1c; }}
  header .meta {{ font-size: 9pt; color: #666; margin-top: 4px; }}
  .severity-badge {{
    display: inline-block; padding: 3px 12px; border-radius: 12px;
    font-weight: bold; font-size: 10pt; color: #fff;
    background: {sev_color}; margin-top: 8px;
  }}
  h2 {{ font-size: 12pt; margin: 20px 0 8px; color: #b71c1c; border-left: 4px solid #b71c1c; padding-left: 8px; }}
  .task-box {{ background: #f5f5f5; border: 1px solid #ddd; border-radius: 5px; padding: 10px 14px; font-size: 10.5pt; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 10pt; }}
  th {{ background: #b71c1c; color: #fff; padding: 7px 10px; text-align: left; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .tinker-tag {{
    background: #b71c1c; color: #fff; font-size: 7.5pt; font-weight: bold;
    padding: 1px 5px; border-radius: 3px; margin-left: 5px;
  }}
  footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 8.5pt; color: #999; }}
  @media print {{
    body {{ padding: 15px 20px; }}
    header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    th, .severity-badge, .tinker-tag {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Tinker AFB — Risk Assessment Report</h1>
  <div class="meta">Assessment ID: {assessment_id} &nbsp;|&nbsp; Generated: {created}</div>
  <div class="severity-badge">Severity: {severity}</div>
</header>

<h2>Task Description</h2>
<div class="task-box">{row['task_description']}</div>

{'<h2>Assessment Criteria</h2><table><thead><tr><th>Criterion</th><th>Value</th></tr></thead><tbody>' + criteria_rows + '</tbody></table>' if criteria_rows else ''}

<h2>PPE Recommendations</h2>
{'<table><thead><tr><th>PPE Item</th><th>Category</th><th>Rationale</th></tr></thead><tbody>' + ppe_rows + '</tbody></table>' if ppe_rows else '<p>No PPE recommendations recorded.</p>'}

<h2>Engineering &amp; Procedural Controls</h2>
{'<table><thead><tr><th>Control</th><th>Rationale</th></tr></thead><tbody>' + ctrl_rows + '</tbody></table>' if ctrl_rows else '<p>No engineering controls recorded.</p>'}

<footer>
  Tinker AFB AI-Based Risk Assessment Database &nbsp;|&nbsp; Printed {datetime.now().strftime('%Y-%m-%d %H:%M')}
  &nbsp;|&nbsp; FOR OFFICIAL USE — verify controls with your supervisor before task execution.
</footer>
</body>
</html>"""

    return HTMLResponse(content=html)
