"""
test_api_integration.py — HTTP-layer integration tests using FastAPI TestClient

These tests spin up a real FastAPI app against a temporary SQLite database
seeded with minimal fixture data.  They exercise the actual HTTP routing,
request validation, response serialization, and DB interactions — the layer
that the pure-unit tests in test_recommend_ppe_endpoint.py do not cover.

spaCy is mocked at the module level so the model does not need to be installed
in CI (lazy loading in analyzer.py means the mock is registered before the
model would otherwise load).
"""

import sys
import json
import sqlite3
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────

API_DIR = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_DIR))

# ── Mock spaCy before any import touches nlp/analyzer.py ─────────────────────
# analyzer.py now lazy-loads spaCy, so registering the mock here is enough.

_mock_spacy = MagicMock()
_mock_doc = MagicMock()
_mock_doc.noun_chunks = []
_mock_doc.__iter__ = lambda self: iter([])
_mock_spacy.load.return_value = MagicMock(return_value=_mock_doc)
sys.modules.setdefault("spacy", _mock_spacy)

# ── Now safe to import app modules ────────────────────────────────────────────

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
from db.session import get_db  # noqa: E402


# ── Minimal schema (SQLite-adapted) ──────────────────────────────────────────

SCHEMA_SQL = """
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
CREATE TABLE IF NOT EXISTS safety_records (
    record_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    location TEXT,
    work_type TEXT,
    hazard_id TEXT,
    exposure_level TEXT,
    temperature_f INTEGER,
    noise_db INTEGER,
    airborne_particles_ppm REAL,
    supervisor TEXT,
    shift TEXT,
    incident_flag INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS safety_record_ppe (
    record_id TEXT,
    ppe_id TEXT,
    PRIMARY KEY (record_id, ppe_id)
);
CREATE TABLE IF NOT EXISTS environmental_docs (
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (doc_id, doc_type)
);
CREATE TABLE IF NOT EXISTS safety_record_docs (
    record_id TEXT,
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (record_id, doc_id, doc_type)
);
CREATE TABLE IF NOT EXISTS ai_assessments (
    assessment_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    task_description TEXT NOT NULL,
    response_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    assessment_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    comment TEXT
);
CREATE TABLE IF NOT EXISTS materials (
    msn TEXT PRIMARY KEY,
    noun TEXT NOT NULL,
    bulk_issue INTEGER
);
CREATE TABLE IF NOT EXISTS shops (
    shop_code TEXT PRIMARY KEY,
    org_symbol TEXT
);
CREATE TABLE IF NOT EXISTS material_authorizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msn TEXT NOT NULL,
    shop_code TEXT NOT NULL,
    process_name TEXT,
    local_process_name TEXT,
    dist_pct REAL,
    max_on_hand INTEGER
);
"""

SEED_SQL = """
INSERT INTO hazards (hazard_id, hazard_label, hazard_category) VALUES
    ('haz_chemical', 'Chemical Exposure', 'Chemical & Airborne'),
    ('haz_noise',    'High Noise',        'Physical Environment');

INSERT INTO ppe (ppe_id, ppe_label, ppe_category) VALUES
    ('ppe_ear_plugs',     'Ear Plugs',     'Hearing Protection'),
    ('ppe_safety_glasses','Safety Glasses','Eye/Face Protection');

INSERT INTO safety_records (record_id, date, location, work_type, hazard_id, exposure_level, shift) VALUES
    ('SR-TEST-001', '2025-01-15', 'Hangar 1', 'Grinding Operations', 'haz_noise',    'High',  'Day'),
    ('SR-TEST-002', '2025-01-20', 'Hangar 2', 'Chemical Cleaning',   'haz_chemical', 'Severe','Night');

INSERT INTO safety_record_ppe (record_id, ppe_id) VALUES
    ('SR-TEST-001', 'ppe_ear_plugs'),
    ('SR-TEST-001', 'ppe_safety_glasses'),
    ('SR-TEST-002', 'ppe_safety_glasses');

INSERT INTO materials (msn, noun, bulk_issue) VALUES
    ('MSN-001', 'Jet Fuel JP-8', 1),
    ('MSN-002', 'Hydraulic Fluid', 0);

INSERT INTO shops (shop_code, org_symbol) VALUES
    ('S100', 'ORG-A'),
    ('S200', 'ORG-B');

INSERT INTO material_authorizations (msn, shop_code, process_name, max_on_hand) VALUES
    ('MSN-001', 'S100', 'Fueling Operations', 50),
    ('MSN-002', 'S200', 'Hydraulic Service', 20);
"""


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SEED_SQL)
    conn.commit()
    conn.close()
    return db_file


@pytest.fixture(scope="session")
def client(test_db_path):
    """TestClient backed by the session-scoped test database."""

    def override_get_db():
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = dict_factory
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Health ────────────────────────────────────────────────────────────────────


def test_health_check(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── Safety Records ────────────────────────────────────────────────────────────


def test_list_safety_records_returns_seeded_data(client):
    r = client.get("/api/v1/safety-records")
    assert r.status_code == 200
    records = r.json()
    assert len(records) == 2
    ids = {rec["record_id"] for rec in records}
    assert "SR-TEST-001" in ids
    assert "SR-TEST-002" in ids


def test_get_single_safety_record(client):
    r = client.get("/api/v1/safety-records/SR-TEST-001")
    assert r.status_code == 200
    rec = r.json()
    assert rec["record_id"] == "SR-TEST-001"
    assert rec["work_type"] == "Grinding Operations"
    ppe_ids = {p["ppe_id"] for p in rec["ppe_required"]}
    assert "ppe_ear_plugs" in ppe_ids


def test_get_safety_record_not_found(client):
    r = client.get("/api/v1/safety-records/NONEXISTENT")
    assert r.status_code == 404


def test_create_safety_record(client):
    payload = {
        "date": "2025-06-01",
        "location": "Building 7",
        "work_type": "Sheet Metal Work",
        "hazard_id": "haz_noise",
        "exposure_level": "Moderate",
        "shift": "Day",
        "incident_flag": False,
        "ppe_ids": ["ppe_ear_plugs"],
    }
    r = client.post("/api/v1/safety-records", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["location"] == "Building 7"
    assert created["work_type"] == "Sheet Metal Work"
    assert created["exposure_level"] == "Moderate"
    assert any(p["ppe_id"] == "ppe_ear_plugs" for p in created["ppe_required"])


def test_create_safety_record_invalid_hazard(client):
    payload = {
        "date": "2025-06-01",
        "location": "Building 7",
        "work_type": "Test",
        "hazard_id": "haz_nonexistent",
        "exposure_level": "Low",
    }
    r = client.post("/api/v1/safety-records", json=payload)
    assert r.status_code == 404


def test_create_safety_record_invalid_exposure_level(client):
    payload = {
        "date": "2025-06-01",
        "location": "X",
        "work_type": "Y",
        "hazard_id": "haz_noise",
        "exposure_level": "Critical",  # not a valid value
    }
    r = client.post("/api/v1/safety-records", json=payload)
    assert r.status_code == 422  # Pydantic validation error


# ── PPE Recommendation ────────────────────────────────────────────────────────


def test_recommend_ppe_by_process_type(client):
    r = client.post("/api/recommend-ppe", json={"process_type": "Grinding"})
    assert r.status_code == 200
    data = r.json()
    assert data["severity_basis"] == "High"
    assert isinstance(data["ppe_recommendations"], list)
    assert isinstance(data["engineering_controls"], list)


def test_recommend_ppe_no_match_returns_404(client):
    r = client.post("/api/recommend-ppe", json={"process_type": "zzz_nonexistent_zzzz"})
    assert r.status_code == 404


def test_recommend_ppe_invalid_severity(client):
    r = client.post("/api/recommend-ppe", json={"process_type": "Grinding", "severity_level": "Critical"})
    assert r.status_code == 400


# ── AI Assessments ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def seeded_assessment_id(client):
    """Insert a synthetic assessment directly and return its ID."""
    assessment_id = str(uuid.uuid4())
    response_json = json.dumps(
        {
            "criteria": {"material_id": None, "process_type": "Grinding", "severity_level": "High"},
            "severity_basis": "High",
            "ppe_recommendations": [
                {"ppe_id": "ppe_ear_plugs", "ppe_type": "Ear Plugs", "ppe_category": "Hearing Protection", "rationale": "test"}
            ],
            "engineering_controls": [],
        }
    )

    def _insert(conn):
        conn.execute(
            "INSERT INTO ai_assessments (assessment_id, created_at, task_description, response_json) VALUES (?,?,?,?)",
            (assessment_id, "2025-06-01T10:00:00", "Grinding steel in Hangar 1", response_json),
        )
        conn.commit()

    # Access the test DB through the overridden dependency
    from db.session import get_db as _get_db

    gen = app.dependency_overrides[_get_db]()
    conn = next(gen)
    _insert(conn)
    try:
        next(gen)
    except StopIteration:
        pass

    return assessment_id


def test_list_ai_assessments(client, seeded_assessment_id):
    r = client.get("/api/v1/ai-assessments")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    ids = {a["assessment_id"] for a in data}
    assert seeded_assessment_id in ids


def test_get_ai_assessment_detail(client, seeded_assessment_id):
    r = client.get(f"/api/v1/ai-assessments/{seeded_assessment_id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["assessment_id"] == seeded_assessment_id
    assert detail["severity_basis"] == "High"
    assert len(detail["ppe_recommendations"]) == 1
    assert detail["ppe_recommendations"][0]["ppe_type"] == "Ear Plugs"


def test_get_ai_assessment_not_found(client):
    r = client.get(f"/api/v1/ai-assessments/{uuid.uuid4()}")
    assert r.status_code == 404


# ── AI Feedback ───────────────────────────────────────────────────────────────


def test_submit_ai_feedback_thumbs_up(client, seeded_assessment_id):
    payload = {"assessment_id": seeded_assessment_id, "feedback_type": "thumbs_up"}
    r = client.post("/api/v1/ai-feedback", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["assessment_id"] == seeded_assessment_id
    assert "feedback_id" in data


def test_submit_ai_feedback_report_requires_comment(client, seeded_assessment_id):
    payload = {"assessment_id": seeded_assessment_id, "feedback_type": "report_inaccuracy"}
    r = client.post("/api/v1/ai-feedback", json=payload)
    assert r.status_code == 422


def test_submit_ai_feedback_unknown_assessment(client):
    payload = {"assessment_id": str(uuid.uuid4()), "feedback_type": "thumbs_down"}
    r = client.post("/api/v1/ai-feedback", json=payload)
    assert r.status_code == 404


# ── Reference Data ────────────────────────────────────────────────────────────


def test_list_ppe_catalog(client):
    r = client.get("/api/v1/ppe")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    categories = {i["ppe_category"] for i in items}
    assert "Hearing Protection" in categories
    assert "Eye/Face Protection" in categories


def test_list_hazards(client):
    r = client.get("/api/v1/hazards")
    assert r.status_code == 200
    hazards = r.json()
    assert len(hazards) == 2
    ids = {h["hazard_id"] for h in hazards}
    assert "haz_chemical" in ids
    assert "haz_noise" in ids


# ── Materials ─────────────────────────────────────────────────────────────────


def test_list_materials(client):
    r = client.get("/api/v1/materials")
    assert r.status_code == 200
    mats = r.json()
    assert len(mats) == 2


def test_list_materials_search(client):
    r = client.get("/api/v1/materials", params={"q": "Jet"})
    assert r.status_code == 200
    mats = r.json()
    assert len(mats) == 1
    assert mats[0]["msn"] == "MSN-001"


def test_get_material_authorizations(client):
    r = client.get("/api/v1/materials/MSN-001/authorizations")
    assert r.status_code == 200
    auths = r.json()
    assert len(auths) == 1
    assert auths[0]["shop_code"] == "S100"
    assert auths[0]["process_name"] == "Fueling Operations"


def test_list_shops(client):
    r = client.get("/api/v1/shops")
    assert r.status_code == 200
    shops = r.json()
    assert len(shops) == 2
    codes = {s["shop_code"] for s in shops}
    assert "S100" in codes


# ── Analyze Task (with mocked NLP) ────────────────────────────────────────────


def test_analyze_task_with_mocked_nlp(client):
    """NLP is mocked to return a specific hazard/process, ensuring the full
    analyze-task → recommend-ppe → persist flow works over HTTP."""
    with patch(
        "routers.safety_records.analyze_task_description",
        return_value=("haz_noise", "Grinding Operations"),
    ):
        r = client.post(
            "/api/v1/analyze-task",
            json={"task_description": "grinding steel with power tools", "severity_level": "High"},
        )
    assert r.status_code == 200
    data = r.json()
    assert "assessment_id" in data
    assert data["severity_basis"] == "High"
    assert isinstance(data["ppe_recommendations"], list)


def test_analyze_task_no_match_returns_400(client):
    with patch(
        "routers.safety_records.analyze_task_description",
        return_value=(None, None),
    ):
        r = client.post(
            "/api/v1/analyze-task",
            json={"task_description": "xyz123 totally unknown", "severity_level": "Low"},
        )
    assert r.status_code == 400
