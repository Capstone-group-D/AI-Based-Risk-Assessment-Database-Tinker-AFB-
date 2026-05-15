# Future Improvements

This document outlines the most impactful improvements recommended for the next phase of development. Items are ordered from most immediately actionable to longer-term.

---

## 1. Migrate from SQLite to PostgreSQL (Production Database)

**Priority: High — Required for Production**

The current system uses SQLite, which is a file-based database suitable for development and demonstration. For a production deployment serving multiple concurrent users, SQLite must be replaced with PostgreSQL (or another server-based RDBMS).

**Why this is straightforward:**  
The schema in `db/schema.sql` was written to be PostgreSQL-compatible. The only change needed is the `id` column in `material_authorizations` — change `INTEGER` to `SERIAL` for a true auto-incrementing sequence.

**Steps to migrate:**

1. Provision a PostgreSQL server (e.g. AWS RDS, Azure Database for PostgreSQL, or a self-hosted instance).
2. Apply the schema:
   ```bash
   psql -U your_user -d risk_assessment_db -f db/schema.sql
   ```
3. Seed the data:
   ```bash
   psql -U your_user -d risk_assessment_db -f db/seed_data.sql
   python3 db/import_aul.py   # re-run AUL import targeting PostgreSQL
   ```
4. Set `DATABASE_URL` in `api/.env`:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/risk_assessment_db
   ```
5. Update `api/db/session.py` to use psycopg2 or asyncpg instead of sqlite3. The SQL queries in the routers are standard SQL and will work without changes.

---

## 2. Improve the NLP / AI Model

**Priority: High — Directly Impacts Accuracy**

The current NLP engine uses spaCy's general-purpose `en_core_web_sm` model for keyword extraction and `thefuzz` for fuzzy matching. This works well for clearly worded descriptions but struggles with:
- Abbreviated military/maintenance terminology
- Multi-hazard tasks
- Short or ambiguous inputs

**Recommended upgrades (in order of effort):**

### 2a. Domain-Specific Entity Recognition
Train a custom spaCy Named Entity Recognizer (NER) on industrial safety text. Label entities such as `CHEMICAL`, `EQUIPMENT`, `PROCESS`, and `HAZARD`. This would dramatically improve keyword extraction accuracy without requiring a new model architecture.

Resources:
- spaCy documentation: https://spacy.io/usage/training
- Training data can be derived from the existing hazard catalog and seed safety records using `prodigy` or manual labeling.

### 2b. Sentence Embedding + Semantic Search
Replace fuzzy string matching with semantic similarity using a sentence transformer model (e.g. `sentence-transformers/all-MiniLM-L6-v2`). Pre-compute embeddings for all hazard labels; at inference time, compute the embedding of the task description and find the nearest neighbor.

This would:
- Handle synonyms and paraphrasing (`"chemical exposure"` → `"hazardous materials contact"`)
- Support multi-hazard matching (top-N results instead of just the best match)
- Eliminate the 50-point threshold hack

### 2c. Classification Model (Longest-Term)
Fine-tune a small transformer (e.g. DistilBERT) on labeled task description → hazard pairs derived from OSHA incident reports and the accumulated `ai_assessments` + `ai_feedback` data. This produces a proper multi-label classifier that can identify multiple hazards per task.

---

## 3. Feed AI Feedback into Model Improvement

**Priority: Medium**

Every thumbs-down and `report_inaccuracy` submission in `ai_feedback` is a labeled training example indicating where the model was wrong. Currently this data is stored but not used.

**Recommended workflow:**
1. Periodically export the feedback table: `GET /api/v1/ai-assessments/export` + join with `ai_feedback`.
2. Review inaccuracy reports to identify systematic errors (e.g. a specific hazard type consistently misidentified).
3. Use these to create labeled training examples for the next model version.
4. Adjust the hazard catalog or PPE rules if the feedback reveals gaps in the reference data.

---

## 4. User Management UI

**Priority: Medium**

When JWT authentication is enabled, users are currently defined as a hard-coded dictionary in `api/core/auth.py`:

```python
USERS = {
    "analyst1": {"password_hash": "...", "role": "analyst", "full_name": "..."},
    ...
}
```

For a production deployment, this should be replaced with:

1. A `users` table in the database (username, hashed password, role, full_name, active flag, last_login).
2. CRUD endpoints for user management (`GET/POST/PUT/DELETE /api/v1/users`) — restricted to supervisor role.
3. A **User Management** page in the frontend for supervisors to add, disable, and reset passwords for accounts.
4. Password hashing using bcrypt (already a dependency — `passlib[bcrypt]` is in `requirements.txt`).

---

## 5. Automated PDF Report Generation

**Priority: Medium**

The system currently generates print-ready HTML reports for individual assessments (`GET /api/v1/ai-assessments/{id}/report`). The next step is scheduled automated reports:

- **Weekly safety summary** — emailed to supervisors every Monday: incident count, top hazards, any new high-severity records
- **Monthly analytics PDF** — full analytics dashboard exported as a PDF
- **Compliance report** — list of all tasks that triggered Tinker AFB procedural controls (Form 493, confined space, etc.) in the past 30 days

Implementation: Use a scheduled task (e.g. `celery beat` or a simple cron job) to call the existing export endpoints and email the results using Python's `smtplib` or a service like SendGrid.

---

## 6. AUL Data Refresh Process

**Priority: Medium**

The AUL material data was imported from a CSV exported on 2026-03-03. As Tinker AFB updates its authorized materials list, the database needs to be refreshed.

**Recommended process:**
1. Obtain the updated AUL CSV from the MXSG system.
2. Place it at `db/seed_data/aul_mxsg_YYYY-MM-DD.csv`.
3. Run `python3 db/import_aul.py` — the script handles deduplication and upserts.

**For production:** The import script should be extended to perform upserts (INSERT OR REPLACE) rather than a full re-import to avoid downtime. Consider adding a `last_updated` timestamp to the `materials` and `shops` tables.

---

## 7. Mobile Application

**Priority: Low-Medium**

Technicians on the shop floor often need to look up PPE requirements on a mobile device. A React Native app using the same FastAPI backend would provide:

- Task Hazard Analysis from a phone
- Offline PPE catalog access (sync when connected)
- Push notifications for safety alerts

The API is already structured for mobile consumption — all responses are JSON, and authentication is token-based.

---

## 8. Integration with AF IT Systems

**Priority: Low (Requires AF IT Coordination)**

Longer-term, the system could be integrated with other Air Force and Tinker AFB information systems:

- **AFMAN / AFOSH standard feeds** — pull the latest Air Force Occupational Safety and Health standards to keep engineering control rationales current.
- **IMDS / G081 maintenance data** — import scheduled maintenance tasks directly so technicians don't have to type descriptions manually.
- **CAC authentication** — replace the current username/password JWT with Common Access Card (CAC) authentication using AF PKI infrastructure.
- **SharePoint / Teams integration** — post safety alerts and weekly reports to unit SharePoint sites or Teams channels.

---

## 9. Audit Log

**Priority: Low**

For compliance and accountability, add an audit log table that records:
- Who created or modified each safety record (requires User Management above)
- When records were exported
- All login and logout events

This is important for environments where records may be subpoenaed or subject to FOIA requests.

Schema addition:
```sql
CREATE TABLE audit_log (
    log_id      TEXT PRIMARY KEY,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id     TEXT,
    action      TEXT,   -- 'create_record', 'export', 'login', etc.
    target_id   TEXT,   -- ID of the affected record
    details     TEXT    -- JSON blob with before/after if applicable
);
```

---

## Summary Priority Matrix

| Improvement | Impact | Effort | Priority |
|---|---|---|---|
| PostgreSQL migration | Critical for production | Low (schema is ready) | **High** |
| Domain NER training | High accuracy gain | Medium | **High** |
| Feed feedback to model | Continuous improvement | Low | **Medium** |
| User management UI | Operational necessity | Medium | **Medium** |
| Automated reports | Supervisor productivity | Medium | **Medium** |
| AUL data refresh process | Data currency | Low | **Medium** |
| Semantic embedding search | Accuracy + robustness | Medium-High | **Medium** |
| Mobile app | Field usability | High | **Low-Medium** |
| AF IT integration | Deep utility | Very High | **Low** |
| Audit log | Compliance | Low | **Low** |
