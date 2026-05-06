"""
Risk Prediction Router
======================
Analyzes historical safety_records to produce a forward-looking risk score and
trend data.  No external ML library required — the model uses weighted incident
rates per exposure level plus a 3-month rolling trend to project near-future
risk.

Algorithm overview
------------------
1. Fetch all safety_records joined with hazards.
2. Compute an incident rate per hazard, per location, and per month.
3. Compute a weighted overall risk score:
     score = Σ (exposure_weight[level] × incident_flag) / Σ exposure_weight[level]
   scaled to 0–100, where higher = more likely incidents going forward.
4. Derive a risk_level label from the score.
5. Return trend data for the last 12 months so the frontend can show whether
   the situation is improving or worsening.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from db.session import get_db
from schemas import MonthlyTrend, PredictionResponse, RiskFactor

router = APIRouter(prefix="/api/v1", tags=["prediction"])

# Higher exposure = higher weight when computing the composite risk score
EXPOSURE_WEIGHTS: dict[str, float] = {
    "Low": 1.0,
    "Moderate": 2.0,
    "High": 3.5,
    "Severe": 5.0,
}


def _risk_level(score: float) -> str:
    if score < 25:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 75:
        return "High"
    return "Severe"


@router.get("/predict-risk", response_model=PredictionResponse)
def predict_risk(
    location: Optional[str] = Query(None, description="Filter to a specific location"),
    work_type: Optional[str] = Query(None, description="Filter to a specific work type"),
    db=Depends(get_db),
):
    """
    Returns a predicted risk score and supporting statistics derived from all
    historical safety records.  Optionally filtered by location or work_type.

    The score is NOT a naive count — it weights each record by exposure level
    so that a few Severe-exposure incidents push the score up more than many
    Low-exposure non-incidents.
    """
    base_sql = """
        SELECT
            sr.record_id,
            sr.date,
            sr.location,
            sr.work_type,
            sr.hazard_id,
            h.hazard_label,
            h.hazard_category,
            sr.exposure_level,
            sr.incident_flag
        FROM safety_records sr
        JOIN hazards h ON sr.hazard_id = h.hazard_id
        WHERE 1=1
    """
    params: list = []
    if location:
        base_sql += " AND sr.location = ?"
        params.append(location)
    if work_type:
        base_sql += " AND sr.work_type = ?"
        params.append(work_type)

    rows = db.execute(base_sql, params).fetchall()

    if not rows:
        return PredictionResponse(
            overall_risk_score=0.0,
            risk_level="Low",
            overall_incident_rate=0.0,
            total_records=0,
            total_incidents=0,
            top_hazards=[],
            top_locations=[],
            monthly_trend=[],
            severity_weights_used=EXPOSURE_WEIGHTS,
            prediction_note="No historical data available for the selected filters.",
        )

    # ── Overall weighted score ────────────────────────────────────────────────
    weighted_incident_sum = 0.0
    weighted_total = 0.0
    total_incidents = 0

    # Per-hazard buckets: {hazard_id: {label, incidents, total}}
    hazard_buckets: dict[str, dict] = defaultdict(lambda: {"label": "", "incidents": 0, "total": 0, "w_incidents": 0.0, "w_total": 0.0})
    location_buckets: dict[str, dict] = defaultdict(lambda: {"label": "", "incidents": 0, "total": 0})

    # Per-month buckets: {"YYYY-MM": {total, incidents}}
    month_buckets: dict[str, dict] = defaultdict(lambda: {"total": 0, "incidents": 0})

    for row in rows:
        w = EXPOSURE_WEIGHTS.get(row["exposure_level"], 1.0)
        incident = bool(row["incident_flag"])

        weighted_total += w
        if incident:
            weighted_incident_sum += w
            total_incidents += 1

        # Hazard aggregation
        hid = row["hazard_id"]
        hazard_buckets[hid]["label"] = row["hazard_label"]
        hazard_buckets[hid]["total"] += 1
        hazard_buckets[hid]["w_total"] += w
        if incident:
            hazard_buckets[hid]["incidents"] += 1
            hazard_buckets[hid]["w_incidents"] += w

        # Location aggregation
        loc = row["location"]
        location_buckets[loc]["label"] = loc
        location_buckets[loc]["total"] += 1
        if incident:
            location_buckets[loc]["incidents"] += 1

        # Monthly aggregation
        try:
            month_key = row["date"][:7]  # "YYYY-MM"
        except Exception:
            month_key = "unknown"
        month_buckets[month_key]["total"] += 1
        if incident:
            month_buckets[month_key]["incidents"] += 1

    raw_score = (weighted_incident_sum / weighted_total * 100) if weighted_total else 0.0

    # ── 3-month rolling trend adjustment ─────────────────────────────────────
    # If the last 3 months show a higher incident rate than the historical
    # average, inflate the score slightly (up to +10 pts) as a forward signal.
    now = datetime.now()
    recent_keys = set()
    for delta in range(3):
        m = now - timedelta(days=delta * 30)
        recent_keys.add(f"{m.year}-{m.month:02d}")

    recent_total = sum(month_buckets[k]["total"] for k in recent_keys if k in month_buckets)
    recent_incidents = sum(month_buckets[k]["incidents"] for k in recent_keys if k in month_buckets)
    recent_rate = (recent_incidents / recent_total) if recent_total else 0.0
    overall_rate = total_incidents / len(rows)
    trend_adjustment = max(0.0, (recent_rate - overall_rate) * 100 * 0.5)  # cap contribution at ~10 pts

    final_score = min(100.0, raw_score + trend_adjustment)

    # ── Top hazards (by weighted incident rate, at least 2 records) ──────────
    top_hazards: List[RiskFactor] = []
    for hid, b in sorted(
        hazard_buckets.items(),
        key=lambda kv: kv[1]["w_incidents"] / max(kv[1]["w_total"], 1),
        reverse=True,
    )[:5]:
        if b["total"] < 2:
            continue
        top_hazards.append(
            RiskFactor(
                label=b["label"],
                incident_count=b["incidents"],
                total_records=b["total"],
                incident_rate=round(b["w_incidents"] / max(b["w_total"], 1), 3),
            )
        )

    # ── Top locations ─────────────────────────────────────────────────────────
    top_locations: List[RiskFactor] = []
    for loc, b in sorted(
        location_buckets.items(),
        key=lambda kv: kv[1]["incidents"] / max(kv[1]["total"], 1),
        reverse=True,
    )[:3]:
        top_locations.append(
            RiskFactor(
                label=loc,
                incident_count=b["incidents"],
                total_records=b["total"],
                incident_rate=round(b["incidents"] / max(b["total"], 1), 3),
            )
        )

    # ── Monthly trend (last 12 months) ────────────────────────────────────────
    monthly_trend: List[MonthlyTrend] = []
    for delta in range(11, -1, -1):
        m = now - timedelta(days=delta * 30)
        key = f"{m.year}-{m.month:02d}"
        bucket = month_buckets.get(key, {"total": 0, "incidents": 0})
        t = bucket["total"]
        i = bucket["incidents"]
        monthly_trend.append(
            MonthlyTrend(
                month=key,
                total=t,
                incidents=i,
                incident_rate=round(i / t, 3) if t else 0.0,
            )
        )

    # ── Prediction note ───────────────────────────────────────────────────────
    if trend_adjustment > 3:
        note = (
            f"Recent 3-month incident rate ({recent_rate:.1%}) is above the "
            f"historical average ({overall_rate:.1%}), suggesting an upward risk "
            "trend. Recommend reviewing controls for top hazard areas."
        )
    elif trend_adjustment < -3:
        note = (
            "Recent incident rate is below the historical average — current "
            "controls appear to be improving safety outcomes."
        )
    else:
        note = (
            f"Incident rate is stable at roughly {overall_rate:.1%}. "
            "Continue monitoring high-exposure tasks and apply Tinker AFB "
            "procedural controls consistently."
        )

    return PredictionResponse(
        overall_risk_score=round(final_score, 1),
        risk_level=_risk_level(final_score),
        overall_incident_rate=round(overall_rate, 3),
        total_records=len(rows),
        total_incidents=total_incidents,
        top_hazards=top_hazards,
        top_locations=top_locations,
        monthly_trend=monthly_trend,
        severity_weights_used=EXPOSURE_WEIGHTS,
        prediction_note=note,
    )
