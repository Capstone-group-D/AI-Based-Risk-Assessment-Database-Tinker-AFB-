# Feature Reference

This document describes every page and feature in the application.

---

## Navigation

The left sidebar provides access to all pages. The header displays the current user (if logged in) and an admin unlock button.

---

## Dashboard — Task Hazard Analysis

**Path:** Default landing page

The Dashboard is the primary tool for safety technicians. It provides two functions:

### Task Hazard Analysis Form

Type a plain-language description of a work task into the text area. Select a severity level and click **Analyze Task**.

The AI engine will:
1. Parse the description using NLP to extract materials (nouns) and actions (verbs).
2. Fuzzy-match against the hazard catalog to identify the most likely hazard.
3. Match the described action against known work types in historical safety records.
4. Return a list of required PPE and engineering controls appropriate for the identified hazard and severity.

**Severity levels:**

| Level | When to Use |
|---|---|
| Low | Routine tasks with minimal hazard exposure |
| Moderate | Standard shop work with controlled chemical or physical hazards |
| High | Tasks with significant exposure, elevated noise, or potential for incident |
| Severe | Tasks with imminent danger, toxic materials, or confined space entry |

**AI Feedback buttons** appear below the result. Use **Thumbs Up / Thumbs Down** to log whether the recommendation was accurate. Use **Report Inaccuracy** to submit a written note about what was wrong — this feedback is stored and available for future model improvement.

### Safety Records

Below the analysis form, all safety records in the database are displayed as cards showing:
- Record ID, hazard label, and exposure level
- Hazard category and work type
- Location, shift, and whether an incident was flagged
- All PPE items associated with the record

---

## Analytics

**Path:** Analytics (sidebar)

Displays charts derived from all safety records in the database:

- **Incident Rate by Hazard Category** — bar chart showing which hazard types cause the most incidents
- **Exposure Level Distribution** — breakdown of records by severity level
- **Incidents Over Time** — monthly trend line
- **Top Locations** — which shop locations appear most frequently in records

Charts update dynamically based on all data in the database.

---

## Risk Assessments

**Path:** Risk Assessments (sidebar)

Two tabs:

### AI Assessment History

Every call to the Task Hazard Analysis form generates an assessment record. This tab lists all past assessments with:
- Date, task description, severity level
- Count of PPE items and engineering controls recommended

Click any row to expand the full recommendation detail. A **Download CSV** button exports the full history.

### Log Safety Record

A form to officially create a new safety record in the database. Fields include:
- Date, location, work type
- Hazard (selected from the reference catalog)
- Exposure level, temperature, noise level, airborne particles
- Supervisor name, shift, and whether an incident occurred
- PPE items assigned (multi-select from the PPE catalog)

> **Note:** When JWT authentication is enabled, only users with the `supervisor` role can create safety records.

---

## PPE Guide

**Path:** PPE Guide (sidebar)

A three-tab reference library.

### Tab 1 — PPE Catalog

All PPE items in the reference database, grouped by category (Eye/Face Protection, Hearing Protection, Hand Protection, etc.). A search bar filters items by name or category.

**Categories include:**
- Eye/Face Protection
- Hearing Protection
- Hand Protection
- Foot Protection
- Head Protection
- Respiratory Protection
- Arc Flash Protection
- Fall Protection

### Tab 2 — Hazard Reference

All hazards in the reference database, grouped by category (Chemical & Airborne, Mechanical & Equipment, Slips/Trips/Falls, etc.). Searchable by name or category.

### Tab 3 — AUL Materials

The Authorized User List (AUL) of hazardous materials maintained by Tinker AFB. Contains 11,000+ materials with shop authorization data.

**Searching:**
- Search by **material name or MSN** (Material Stock Number) in the left field
- Filter by **shop code** in the right field (e.g., type `553` to see all materials authorized for Shop 553)
- Both filters can be used together
- An active shop code filter shows a blue badge below the search bar; click **✕** to clear it

**Expanding a material row** shows:
- All shop authorizations for that material: shop code, process name, local process name, distribution %, and max on hand quantity
- When a shop code filter is active, the matching shop's row is highlighted in gold
- A **Recommend PPE →** button that runs the PPE recommendation engine against that specific material

---

## Risk Prediction

**Path:** Risk Prediction (sidebar)

Analyzes all historical safety records to produce a forward-looking risk assessment.

**Output includes:**
- **Overall Risk Score** (0–100, weighted by exposure level severity)
- **Risk Level** label: Low / Moderate / High / Severe
- **Overall Incident Rate** — fraction of records with an incident flag
- **Top 5 Hazards** by weighted incident rate
- **Top 3 Locations** by incident rate
- **12-Month Trend** chart

**Optional filters:** Filter the analysis to a specific location or work type using the dropdowns at the top.

The score is calculated using exposure-level weights (Low=1×, Moderate=2×, High=3.5×, Severe=5×) so that a small number of high-severity incidents correctly push the score up more than many low-severity non-incidents.

---

## Pollution Prevention

**Path:** Pollution Prevention (sidebar)

Tracks the facility's pollution prevention initiatives with two views:

- **Opportunities list** — all logged pollution prevention opportunities with status (Identified / Planned / Implementing / Completed), priority, expected waste reduction %, and responsible party
- **Summary stats** — total initiatives, completion rate, average expected reduction

---

## AI Feedback Panel

**Path:** AI Feedback (sidebar)

A dedicated view of all submitted AI feedback (thumbs up, thumbs down, and inaccuracy reports), linked back to the original assessment. This data is intended for periodic review to identify where the NLP/recommendation engine needs improvement.

---

## Authentication and Roles

The system supports three modes. The active mode is reported by the health endpoint (`GET /api/v1/health → auth_mode`).

| Mode | Behavior |
|---|---|
| `open` | No credentials required. All features accessible to all users. |
| `api_key` | API key required in `X-API-Key` header. Frontend reads from `VITE_API_KEY`. |
| `jwt` | Login screen shown. Three roles available (see below). |

**JWT roles:**

| Role | Permissions |
|---|---|
| `viewer` | Read-only access to all data |
| `analyst` | Can run Task Hazard Analysis |
| `supervisor` | Full access including creating safety records |

Users are defined in `api/core/auth.py` in the `USERS` dictionary. See [Future Improvements](./07_future_improvements.md) for notes on adding a proper user management UI.
