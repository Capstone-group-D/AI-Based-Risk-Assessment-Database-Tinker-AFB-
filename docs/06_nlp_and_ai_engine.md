# AI / NLP Engine

This document explains how the Task Hazard Analysis feature works under the hood.

---

## High-Level Flow

```
User types task description
         │
         ▼
   extract_keywords()          ← spaCy NLP pipeline
   (api/nlp/analyzer.py)
         │
   Returns: actions_str, materials_str
         │
         ▼
   Fuzzy match against hazard catalog    ← thefuzz library
   (hazard_label → hazard_id)
         │
   Fuzzy match against known work types
   (safety_records.work_type)
         │
         ▼
   recommend_ppe()             ← api/routers/safety_records.py
         │
   Filter historical records by hazard_id + work_type + severity
         │
   Collect unique PPE from matched records
   Apply ENGINEERING_CONTROL_RULES (by hazard_category)
   Apply TINKER_PROCEDURAL_CONTROLS (by hazard_id)
         │
         ▼
   PPERecommendationResponse
   (persisted as ai_assessments row)
```

---

## Step 1 — Keyword Extraction (spaCy)

**File:** `api/nlp/analyzer.py`  
**Function:** `extract_keywords(description: str)`

spaCy's `en_core_web_sm` model is used to parse the input text. The pipeline:

1. **Noun chunks** — multi-word noun phrases (e.g. `"steel beams"`, `"grinding wheel"`) are extracted as materials.
2. **Individual nouns and proper nouns** — any NOUN or PROPN token not already captured in a noun chunk is also added to materials.
3. **Verbs** — VERB tokens are lemmatized (e.g. `"welding"` → `"weld"`) and collected as actions.

The function returns two strings:
- `actions_str` — space-joined verb lemmas (e.g. `"weld grind cut"`)
- `materials_str` — space-joined noun phrases (e.g. `"steel beam grinding wheel second floor"`)

The spaCy model is loaded **lazily** (on first call) so the API starts up quickly and the model does not need to be loaded during automated tests.

---

## Step 2 — Fuzzy Hazard Matching (thefuzz)

**File:** `api/nlp/analyzer.py`  
**Function:** `analyze_task_description(description: str, db)`

The combined string `materials_str + " " + description` is fuzzy-matched against all `hazard_label` values in the database using `thefuzz.process.extractOne`.

- If the best match score is **≥ 50**, the corresponding `hazard_id` is used.
- If no match exceeds 50, `hazard_id` is set to `None`.

Similarly, `actions_str + " " + description` is matched against all distinct `work_type` values from historical safety records.

- If the best match score is **≥ 50**, that `work_type` is used as `process_type`.
- If no match exceeds 50, `process_type` is set to `None`.

The 50-point threshold balances recall and precision for short industrial descriptions. Lowering it will yield more matches but with more false positives; raising it will reduce false positives but miss some valid descriptions.

---

## Step 3 — PPE Recommendation Engine

**File:** `api/routers/safety_records.py`  
**Function:** `recommend_ppe(payload: PPERecommendationRequest, db)`

### Record Filtering

1. All safety records are loaded from the database.
2. Records are filtered to those matching the identified `hazard_id` (if found).
3. Records are filtered to those matching the identified `process_type` (if found).
4. If no records match, a 404 is returned, and the caller retries with just one dimension (hazard-only or process-only).

### Severity Filtering

The `severity_level` from the request is used as the minimum threshold. Records with exposure levels *below* the requested severity are excluded. This ensures that a High-severity analysis pulls PPE from High and Severe historical records only.

**Severity ranking:** Low (1) < Moderate (2) < High (3) < Severe (4)

### PPE Collection

From the severity-filtered records, all unique PPE items are collected into a catalog (deduped by `ppe_id`). For each item, a rationale string is generated explaining which hazard, work type, and severity level triggered the recommendation.

### Engineering Controls

**Generic controls** (`ENGINEERING_CONTROL_RULES` dictionary):  
Keyed by `hazard_category`. When a matched record belongs to a category that has engineering controls defined, those controls are added to the response. Controls are deduped by `control_type`.

**Tinker AFB procedural controls** (`TINKER_PROCEDURAL_CONTROLS_BY_HAZARD_ID` dictionary):  
Keyed by exact `hazard_id`. These are mandatory procedural requirements derived directly from the Tinker AFB Risk Assessment Form (Form 493, confined space permits, vehicle inspections, hot work fire watch requirements, etc.). They are marked with `source = "TINKER"` and displayed with a red **TINKER AFB FORM** badge in the UI.

---

## Engineering Control Rule Tables

### Generic Controls by Hazard Category

| Hazard Category | Controls Applied |
|---|---|
| Chemical & Airborne | Local Exhaust Ventilation; Closed Transfer / Secondary Containment |
| Physical Environment | Noise Monitoring & Hearing Conservation Program; Environmental Controls (HVAC / Heat Stress Monitoring) |
| Mechanical & Equipment | Lockout/Tagout (LOTO) Procedures; Machine Guarding |
| Slips, Trips, Falls & Work at Height | Fall Protection System; Walking Surface Management |
| Ergonomics & Human Factors | Ergonomic Job Hazard Analysis; Mechanical Lifting Assists |
| Sharp Objects | Sharps Management Program |
| Biological | Pest Control / Site Hazard Assessment |

### Tinker AFB Procedural Controls by Hazard ID

| Hazard | Mandatory Tinker Controls |
|---|---|
| `haz_electrical_mechanical_energy` | LOTO Form 493; Depressure/Drain |
| `haz_gravity_potential_energy` | LOTO Block/Shore Loads; Crane/Hoist Inspection; Rigging Sling/Chain Inspection |
| `haz_heavy_load_secure` | LOTO Block/Shore Loads; Crane/Hoist Inspection; Rigging Inspection |
| `haz_machine_guards` | LOTO Form 493 |
| `haz_pinch_points` | LOTO Form 493 |
| `haz_reaction_pressure_vacuum` | LOTO Form 493; Depressure/Drain |
| `haz_congestion_tight_spaces` | Confined Space — Gas Test; Non-Permit; Permit Required |
| `haz_ventilation_fumes_mist_dust` | Confined Space — Gas Test |
| `haz_fire_explosion` | Hot Work — Standby/Fire Watch |
| `haz_hazardous_materials_exposure` | Confined Space — Gas Test |
| `haz_fall_from_elevation` | Vehicle Inspection — Scissor Lift; Boom Lift |
| `haz_climbing_crawling_bending` | Vehicle Inspection — Scissor Lift; Boom Lift |
| `haz_path_of_travel` | Vehicle Inspection — Cart/Mule/Gator |
| `haz_overhead_work_falling_objects` | Crane/Hoist Inspection; Rigging Sling/Chain Inspection |

---

## AUL Material PPE Recommendation

**File:** `api/routers/materials.py`  
**Endpoint:** `POST /api/v1/materials/recommend-ppe`

When the user clicks "Recommend PPE →" on an AUL material in the PPE Guide, a separate pipeline runs:

1. The material is looked up by MSN in the `materials` table to get its `noun` (name).
2. The material noun is fuzzy-matched against the hazard catalog (threshold: 40 — lower than the task analysis threshold because material names are shorter and more specific).
3. Process names from `material_authorizations` for that MSN are fuzzy-matched against known `work_type` values in safety records.
4. The result is passed to the same `recommend_ppe()` function used by the task analysis pipeline.
5. Authorized shop codes for the material are appended to the response.

---

## Known Limitations

1. **Accuracy depends on historical data volume.** The recommendation engine draws PPE from historical safety records. A database with few records will produce sparse recommendations. The seed data provides a baseline, but accuracy improves as real records are added over time.

2. **Short or ambiguous descriptions may not match.** If a task description does not contain enough recognizable nouns or verbs, the fuzzy matching may not reach the 50-point confidence threshold. In this case, the API returns a 400 error asking the user to be more specific.

3. **One hazard matched at a time.** The current engine identifies a single best-matching hazard per task. Real-world tasks often involve multiple hazard types simultaneously. A multi-label classifier would improve this — see [Future Improvements](./07_future_improvements.md).

4. **No learning from feedback.** The thumbs-up / thumbs-down / report-inaccuracy data is stored in `ai_feedback` but is not currently fed back into the model. This data is valuable for future fine-tuning.

5. **spaCy `en_core_web_sm` is a general-purpose model.** It was not trained on industrial safety or military maintenance vocabulary. Domain-specific terms may not be parsed as well as everyday language. A fine-tuned model would perform significantly better — see [Future Improvements](./07_future_improvements.md).
