import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "risk_assessment.db"

_ENSURE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS hazards (
    hazard_id TEXT PRIMARY KEY,
    hazard_label TEXT NOT NULL,
    hazard_category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ppe (
    ppe_id TEXT PRIMARY KEY,
    ppe_label TEXT NOT NULL,
    ppe_category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS environmental_docs (
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (doc_id, doc_type)
);
CREATE TABLE IF NOT EXISTS safety_records (
    record_id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    location TEXT,
    work_type TEXT,
    hazard_id TEXT REFERENCES hazards(hazard_id),
    exposure_level TEXT CHECK (exposure_level IN ('Low','Moderate','High','Severe')),
    temperature_f INT,
    noise_db INT,
    airborne_particles_ppm DECIMAL(6,2),
    supervisor TEXT,
    shift TEXT CHECK (shift IN ('Day','Swing','Night')),
    incident_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS safety_record_ppe (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    ppe_id TEXT REFERENCES ppe(ppe_id),
    PRIMARY KEY (record_id, ppe_id)
);
CREATE TABLE IF NOT EXISTS safety_record_docs (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (record_id, doc_id, doc_type),
    FOREIGN KEY (doc_id, doc_type) REFERENCES environmental_docs(doc_id, doc_type)
);
CREATE TABLE IF NOT EXISTS materials (
    msn TEXT PRIMARY KEY,
    noun TEXT NOT NULL,
    bulk_issue BOOLEAN
);
CREATE TABLE IF NOT EXISTS shops (
    shop_code TEXT PRIMARY KEY,
    org_symbol TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS material_authorizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msn TEXT NOT NULL REFERENCES materials(msn),
    shop_code TEXT NOT NULL REFERENCES shops(shop_code),
    process_name TEXT,
    local_process_name TEXT,
    dist_pct REAL,
    max_on_hand INTEGER
);
CREATE TABLE IF NOT EXISTS ai_assessments (
    assessment_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_description TEXT NOT NULL,
    response_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessment_id TEXT NOT NULL REFERENCES ai_assessments(assessment_id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL CHECK (
        feedback_type IN ('thumbs_up','thumbs_down','report_inaccuracy')
    ),
    comment TEXT
);
CREATE INDEX IF NOT EXISTS idx_safety_date ON safety_records(date);
CREATE INDEX IF NOT EXISTS idx_safety_hazard ON safety_records(hazard_id);
CREATE INDEX IF NOT EXISTS idx_safety_incident ON safety_records(incident_flag);
CREATE INDEX IF NOT EXISTS idx_matauth_shop_code ON material_authorizations(shop_code);
CREATE INDEX IF NOT EXISTS idx_matauth_msn ON material_authorizations(msn);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_assessment_id ON ai_feedback(assessment_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_created_at ON ai_feedback(created_at);
CREATE TABLE IF NOT EXISTS waste_categories (
    waste_category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    hazard_class TEXT,
    disposal_method TEXT,
    epa_code TEXT
);
CREATE TABLE IF NOT EXISTS waste_records (
    waste_record_id TEXT PRIMARY KEY,
    date_generated TEXT,
    location TEXT,
    waste_category_id TEXT REFERENCES waste_categories(waste_category_id),
    quantity_kg REAL,
    quantity_unit TEXT DEFAULT 'kg',
    generator_name TEXT,
    process_type TEXT,
    container_type TEXT,
    storage_location TEXT,
    disposal_date TEXT,
    disposal_method TEXT,
    recycler_name TEXT,
    cost_usd REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS recycling_opportunities (
    opportunity_id TEXT PRIMARY KEY,
    waste_category_id TEXT REFERENCES waste_categories(waste_category_id),
    opportunity_name TEXT NOT NULL,
    description TEXT,
    recycler_contact TEXT,
    estimated_value_per_kg REAL,
    environmental_impact TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS pollution_prevention_opportunities (
    opportunity_id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    task_description TEXT,
    waste_category_id TEXT REFERENCES waste_categories(waste_category_id),
    prevention_method TEXT,
    expected_reduction_percent REAL,
    implementation_cost_usd REAL,
    payback_period_months INTEGER,
    priority_level TEXT,
    responsible_party TEXT,
    status TEXT DEFAULT 'Identified',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS task_waste_relationships (
    task_name TEXT NOT NULL,
    waste_category_id TEXT REFERENCES waste_categories(waste_category_id),
    average_quantity_kg REAL,
    frequency TEXT,
    PRIMARY KEY (task_name, waste_category_id)
);
"""


def _init_schema_once() -> None:
    """Create all tables on startup — runs once when the module is first imported."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        for statement in _ENSURE_TABLES_SQL.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


# Run at import time so every worker process gets a fully migrated DB
# before it starts serving requests.
_init_schema_once()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    """FastAPI dependency — yields a dict-row SQLite connection.

    check_same_thread=False is required because FastAPI runs sync endpoints
    in a thread pool: the dependency may be resolved in a different thread
    than the one that executes the endpoint function.  Each request gets its
    own connection that is closed immediately after, so this is safe.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = dict_factory
    try:
        yield conn
    finally:
        conn.close()
