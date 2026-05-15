# API Reference

All endpoints are served from `http://localhost:8000`. The interactive Swagger UI with live request testing is available at `http://localhost:8000/docs`.

## Authentication

When `API_KEY` is set in `api/.env`, all data routes require the following request header:
```
X-API-Key: <your-api-key>
```

When `JWT_SECRET_KEY` is set, users must first authenticate via `POST /api/v1/auth/login` and include the returned token as:
```
Authorization: Bearer <access_token>
```

The health endpoint never requires authentication.

---

## Health

### `GET /api/v1/health`
Returns the current API status and active authentication mode.

**Response:**
```json
{
  "status": "ok",
  "message": "API online",
  "version": "0.4.0",
  "auth_mode": "open"
}
```
`auth_mode` is one of `"open"`, `"api_key"`, or `"jwt"`.

---

## Safety Records

### `GET /api/v1/safety-records`
Returns all safety records with their associated hazard labels and PPE assignments.

**Response:** Array of `SafetyRecord` objects.

```json
[
  {
    "record_id": "SR-A1B2C3D4",
    "date": "2025-03-14",
    "location": "Building 3220",
    "work_type": "Welding",
    "hazard_id": "haz_fire_explosion",
    "hazard_label": "Fire / Explosion Risk",
    "hazard_category": "Mechanical & Equipment",
    "exposure_level": "High",
    "temperature_f": 95,
    "noise_db": 92,
    "airborne_particles_ppm": null,
    "supervisor": "SSgt Johnson",
    "shift": "Day",
    "incident_flag": false,
    "ppe_required": [
      { "ppe_id": "ppe_face_shield", "ppe_label": "Face Shield", "ppe_category": "Eye/Face Protection" }
    ]
  }
]
```

---

### `GET /api/v1/safety-records/{record_id}`
Returns a single safety record by its ID (e.g. `SR-A1B2C3D4`).

**Response:** Single `SafetyRecord` object.  
**404** if not found.

---

### `POST /api/v1/safety-records`
Creates a new safety record.

> **Requires:** `supervisor` role when JWT auth is enabled.

**Request body:**
```json
{
  "date": "2025-03-14",
  "location": "Building 3220",
  "work_type": "Welding",
  "hazard_id": "haz_fire_explosion",
  "exposure_level": "High",
  "temperature_f": 95,
  "noise_db": 92,
  "airborne_particles_ppm": null,
  "supervisor": "SSgt Johnson",
  "shift": "Day",
  "incident_flag": false,
  "ppe_ids": ["ppe_face_shield", "ppe_gloves_heat"]
}
```

**Response (201):** The created `SafetyRecord`.

---

### `GET /api/v1/safety-records/export`
Downloads all safety records as a CSV file.

**Response:** `text/csv` attachment — `tinker_safety_records_YYYYMMDD.csv`

---

## PPE Recommendation Engine

### `POST /api/recommend-ppe`
Recommends PPE and engineering controls based on a hazard ID or process type.

**Request body** (at least one of `material_id` or `process_type` required):
```json
{
  "material_id": "haz_chemical_solvent",
  "process_type": "Parts Cleaning",
  "severity_level": "High"
}
```

**Response:**
```json
{
  "criteria": { "material_id": "...", "process_type": "...", "severity_level": "High" },
  "severity_basis": "High",
  "ppe_recommendations": [
    {
      "ppe_id": "ppe_respirator_half",
      "ppe_type": "Half-Face Air-Purifying Respirator",
      "ppe_category": "Respiratory Protection",
      "rationale": "Recommended for Chemical Solvent during Parts Cleaning at High severity..."
    }
  ],
  "engineering_controls": [
    {
      "control_type": "Local Exhaust Ventilation",
      "rationale": "Capture chemical vapors at the source...",
      "control_id": null,
      "source": null
    }
  ]
}
```

---

### `POST /api/v1/analyze-task`
Analyzes a plain-language task description using NLP and returns PPE recommendations.

> **Requires:** `analyst` role when JWT auth is enabled.

**Request body:**
```json
{
  "task_description": "Welding steel beams on the second floor with grinding and cutting operations.",
  "severity_level": "Moderate"
}
```

**Response:** Same as `POST /api/recommend-ppe` plus:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  ...
}
```
The `assessment_id` is used to submit feedback and retrieve the assessment later.

---

## AI Assessment History

### `GET /api/v1/ai-assessments`
Returns a summary list of all AI assessments, newest first.

**Response:** Array of `AIAssessmentSummary` objects with `assessment_id`, `created_at`, `task_description`, `severity_basis`, `ppe_count`, `control_count`.

---

### `GET /api/v1/ai-assessments/{assessment_id}`
Returns the full recommendation detail for a single assessment.

---

### `GET /api/v1/ai-assessments/{assessment_id}/report`
Returns a print-ready HTML page for the assessment. Open in a browser and use Ctrl/Cmd+P → Save as PDF.

---

### `GET /api/v1/ai-assessments/export`
Downloads all assessments as a CSV summary.

**Response:** `text/csv` attachment — `tinker_assessments_YYYYMMDD.csv`

---

## AI Feedback

### `POST /api/v1/ai-feedback`
Submits feedback on an AI-generated assessment.

**Request body:**
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback_type": "thumbs_up",
  "comment": null
}
```

`feedback_type` must be one of: `"thumbs_up"`, `"thumbs_down"`, `"report_inaccuracy"`.  
`comment` is required when `feedback_type` is `"report_inaccuracy"`.

**Response (201):**
```json
{
  "feedback_id": "fb-xxxxxxxx",
  "assessment_id": "...",
  "created_at": "2025-03-14T10:22:00"
}
```

---

## Reference Data

### `GET /api/v1/ppe`
Returns all PPE items from the catalog, sorted by category then label.

**Response:** Array of `{ ppe_id, ppe_label, ppe_category }`.

---

### `GET /api/v1/hazards`
Returns all hazards from the catalog, sorted by category then label.

**Response:** Array of `{ hazard_id, hazard_label, hazard_category }`.

---

## AUL Materials

### `GET /api/v1/materials`
Returns AUL materials. Capped at 200 rows — use query parameters to narrow results.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `q` | string | Filter by material name or MSN (partial match) |
| `shop_code` | string | Filter to materials authorized for a specific shop (e.g. `553`) |

**Response:** Array of `{ msn, noun, bulk_issue }`.

---

### `GET /api/v1/materials/{msn}/authorizations`
Returns all shop authorizations for a material by MSN.

**Response:** Array of `{ id, msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand }`.

---

### `POST /api/v1/materials/recommend-ppe`
Looks up a material by MSN, fuzzy-matches its name against the hazard catalog, and returns PPE recommendations.

**Request body:**
```json
{
  "msn": "6850-01-123-4567",
  "severity_level": "Moderate"
}
```

**Response:** Same as `POST /api/recommend-ppe` plus `msn`, `material_name`, `matched_hazard_label`, and `authorized_shops`.

---

### `GET /api/v1/shops`
Returns all shops from the AUL reference table.

**Response:** Array of `{ shop_code, org_symbol }`.

---

## Risk Prediction

### `GET /api/v1/predict-risk`
Returns a weighted risk score and trend analysis derived from all historical safety records.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `location` | string | Filter to a specific location |
| `work_type` | string | Filter to a specific work type |

**Response:**
```json
{
  "overall_risk_score": 34.7,
  "risk_level": "Moderate",
  "overall_incident_rate": 0.182,
  "total_records": 220,
  "total_incidents": 40,
  "top_hazards": [...],
  "top_locations": [...],
  "monthly_trend": [...],
  "severity_weights_used": { "Low": 1.0, "Moderate": 2.0, "High": 3.5, "Severe": 5.0 },
  "prediction_note": "Incident rate is stable at roughly 18.2%..."
}
```

---

## Authentication (JWT)

### `POST /api/v1/auth/login`
Authenticates a user and returns access and refresh tokens.

**Request body:**
```json
{ "username": "analyst1", "password": "your-password" }
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "role": "analyst",
  "username": "analyst1",
  "full_name": "Jane Smith"
}
```

---

### `POST /api/v1/auth/refresh`
Exchanges a refresh token for a new access token.

**Request body:** `{ "refresh_token": "eyJ..." }`

---

### `GET /api/v1/auth/me`
Returns the currently authenticated user's info.

**Response:** `{ username, full_name, role }`
