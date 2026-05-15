# Database Schema

The application uses **SQLite** for development and demonstration. The schema is written to be **PostgreSQL-compatible** — see [Future Improvements](./07_future_improvements.md) for migration guidance.

The schema is defined in `db/schema.sql`. The database is initialized by running `python3 db/init_db.py` from the repo root.

---

## Core Safety Tables

### `hazards`
The reference catalog of all known hazard types. Populated from `db/seed_data.sql`.

| Column | Type | Description |
|---|---|---|
| `hazard_id` | TEXT (PK) | Unique identifier, e.g. `haz_fire_explosion` |
| `hazard_label` | TEXT | Human-readable label, e.g. `"Fire / Explosion Risk"` |
| `hazard_category` | TEXT | Broad category, e.g. `"Mechanical & Equipment"` |

**Hazard categories used in the seed data:**
- Chemical & Airborne
- Mechanical & Equipment
- Physical Environment
- Slips, Trips, Falls & Work at Height
- Ergonomics & Human Factors
- Sharp Objects
- Biological

---

### `ppe`
The reference catalog of all personal protective equipment types.

| Column | Type | Description |
|---|---|---|
| `ppe_id` | TEXT (PK) | Unique identifier, e.g. `ppe_face_shield` |
| `ppe_label` | TEXT | Human-readable label, e.g. `"Face Shield"` |
| `ppe_category` | TEXT | Category, e.g. `"Eye/Face Protection"` |

---

### `safety_records`
The main fact table. One row per logged safety event.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `record_id` | TEXT (PK) | — | Unique ID, format `SR-XXXXXXXX` |
| `date` | DATE | — | Date of the safety event |
| `location` | TEXT | Yes | Shop or building location |
| `work_type` | TEXT | Yes | Type of work performed |
| `hazard_id` | TEXT (FK → hazards) | Yes | Associated hazard |
| `exposure_level` | TEXT | Yes | One of: `Low`, `Moderate`, `High`, `Severe` |
| `temperature_f` | INT | Yes | Ambient temperature in °F |
| `noise_db` | INT | Yes | Noise level in decibels |
| `airborne_particles_ppm` | DECIMAL(6,2) | Yes | Airborne particle concentration |
| `supervisor` | TEXT | Yes | Supervising personnel |
| `shift` | TEXT | Yes | One of: `Day`, `Swing`, `Night` |
| `incident_flag` | BOOLEAN | — | `true` if an incident occurred (default `false`) |
| `created_at` | TIMESTAMP | — | Auto-set on insert |

**Indexes:** `date`, `hazard_id`, `incident_flag`

---

### `safety_record_ppe`
Junction table linking safety records to their required PPE items.

| Column | Type | Description |
|---|---|---|
| `record_id` | TEXT (FK → safety_records) | |
| `ppe_id` | TEXT (FK → ppe) | |
| Primary key | `(record_id, ppe_id)` | |

Cascades on delete: removing a safety record also removes its PPE associations.

---

## AI / NLP Tables

### `ai_assessments`
One row per AI-generated recommendation returned by `POST /api/v1/analyze-task`.

| Column | Type | Description |
|---|---|---|
| `assessment_id` | TEXT (PK) | UUID |
| `created_at` | TIMESTAMP | Auto-set on insert |
| `task_description` | TEXT | The original plain-language task input |
| `response_json` | TEXT | Full recommendation response, stored as JSON |

---

### `ai_feedback`
User feedback submitted on AI assessment results.

| Column | Type | Description |
|---|---|---|
| `feedback_id` | TEXT (PK) | Auto-generated |
| `created_at` | TIMESTAMP | Auto-set on insert |
| `assessment_id` | TEXT (FK → ai_assessments) | The assessment being rated |
| `feedback_type` | TEXT | One of: `thumbs_up`, `thumbs_down`, `report_inaccuracy` |
| `comment` | TEXT | Required only for `report_inaccuracy` |

**Indexes:** `assessment_id`, `created_at`

---

## AUL (Authorized User List) Tables

These tables are populated from the Tinker AFB AUL CSV file during `db/init_db.py`.

### `materials`
Hazardous materials authorized for use at Tinker AFB.

| Column | Type | Description |
|---|---|---|
| `msn` | TEXT (PK) | Material Stock Number (national stock number format) |
| `noun` | TEXT | Material name / noun description |
| `bulk_issue` | BOOLEAN | Whether the material is issued in bulk quantities |

---

### `shops`
Tinker AFB shop locations that are authorized to handle hazardous materials.

| Column | Type | Description |
|---|---|---|
| `shop_code` | TEXT (PK) | Short shop identifier, e.g. `553` |
| `org_symbol` | TEXT | Organizational symbol for the shop |

---

### `material_authorizations`
The fact table linking materials to the shops authorized to use them, along with process details.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment |
| `msn` | TEXT (FK → materials) | |
| `shop_code` | TEXT (FK → shops) | |
| `process_name` | TEXT | Standard process name |
| `local_process_name` | TEXT | Tinker-specific local process name |
| `dist_pct` | NUMERIC(7,4) | Distribution percentage (stored as literal %, e.g. `33.3333`) |
| `max_on_hand` | INTEGER | Maximum authorized quantity on hand |

**Indexes:** `shop_code`, `msn`

> **Scale:** The AUL import loads approximately 11,025 materials, 354 shops, and 26,759 authorization rows.

---

## Hazardous Waste Tables

### `waste_categories`
Reference table for hazardous waste types.

| Column | Type | Description |
|---|---|---|
| `waste_category_id` | TEXT (PK) | |
| `category_name` | TEXT | e.g. `"Spent Solvent"` |
| `hazard_class` | TEXT | e.g. `"Flammable"`, `"Corrosive"` |
| `disposal_method` | TEXT | e.g. `"Incineration"`, `"Recycling"` |
| `epa_code` | TEXT | EPA waste code if applicable |

---

### `waste_records`
Individual waste generation events.

| Column | Type | Description |
|---|---|---|
| `waste_record_id` | TEXT (PK) | |
| `date_generated` | DATE | |
| `location` | TEXT | Shop/building location |
| `waste_category_id` | TEXT (FK → waste_categories) | |
| `quantity_kg` | DECIMAL(10,2) | Quantity in kilograms |
| `quantity_unit` | TEXT | Default `"kg"` |
| `generator_name` | TEXT | Person or department |
| `process_type` | TEXT | e.g. `"Engine Wash"` |
| `container_type` | TEXT | e.g. `"55-gallon drum"` |
| `storage_location` | TEXT | |
| `disposal_date` | DATE | |
| `disposal_method` | TEXT | |
| `recycler_name` | TEXT | If recycled |
| `cost_usd` | DECIMAL(10,2) | |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

---

### `recycling_opportunities`
Potential recycling pathways for waste categories.

| Column | Type | Description |
|---|---|---|
| `opportunity_id` | TEXT (PK) | |
| `waste_category_id` | TEXT (FK → waste_categories) | |
| `opportunity_name` | TEXT | |
| `description` | TEXT | |
| `recycler_contact` | TEXT | |
| `estimated_value_per_kg` | DECIMAL(8,2) | Economic value |
| `environmental_impact` | TEXT | |
| `is_active` | BOOLEAN | |
| `created_at` | TIMESTAMP | |

---

### `pollution_prevention_opportunities`
Initiatives to reduce waste generation at the source.

| Column | Type | Description |
|---|---|---|
| `opportunity_id` | TEXT (PK) | |
| `task_name` | TEXT | e.g. `"Engine Wash"` |
| `task_description` | TEXT | |
| `waste_category_id` | TEXT (FK → waste_categories) | Optional |
| `prevention_method` | TEXT | |
| `expected_reduction_percent` | DECIMAL(5,2) | |
| `implementation_cost_usd` | DECIMAL(10,2) | |
| `payback_period_months` | INTEGER | |
| `priority_level` | TEXT | One of: `Low`, `Medium`, `High`, `Critical` |
| `responsible_party` | TEXT | |
| `status` | TEXT | One of: `Identified`, `Planned`, `Implementing`, `Completed` |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

---

### `task_waste_relationships`
Links task types to the waste categories they typically generate.

| Column | Type | Description |
|---|---|---|
| `task_name` | TEXT (PK) | |
| `waste_category_id` | TEXT (FK → waste_categories) (PK) | |
| `average_quantity_kg` | DECIMAL(8,2) | |
| `frequency` | TEXT | e.g. `"Daily"`, `"Weekly"` |

---

## SQLite vs PostgreSQL Differences

The development database is SQLite. The schema is written to be largely compatible with PostgreSQL, with two known differences:

| Feature | SQLite | PostgreSQL |
|---|---|---|
| Auto-increment primary key | `id INTEGER` (auto-increment in SQLite) | `id SERIAL PRIMARY KEY` |
| `BOOLEAN` type | Stored as 0/1 integer | Native boolean |
| `DECIMAL` precision | Approximate | Exact |

When migrating to PostgreSQL, change `id INTEGER` to `id SERIAL PRIMARY KEY` in `material_authorizations`. Everything else migrates cleanly. See [Future Improvements](./07_future_improvements.md) for step-by-step migration guidance.
