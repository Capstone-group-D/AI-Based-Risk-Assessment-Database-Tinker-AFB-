-- ============================================
-- AI Safety Risk Assessment Database Schema
-- Synthetic seed data compatible
-- Target: PostgreSQL
-- ============================================

-- ======================
-- Hazards Reference Table
-- ======================
CREATE TABLE IF NOT EXISTS hazards (
    hazard_id TEXT PRIMARY KEY,
    hazard_label TEXT NOT NULL,
    hazard_category TEXT NOT NULL
);

-- ======================
-- PPE Reference Table
-- ======================
CREATE TABLE IF NOT EXISTS ppe (
    ppe_id TEXT PRIMARY KEY,
    ppe_label TEXT NOT NULL,
    ppe_category TEXT NOT NULL
);

-- ======================
-- Environmental Documentation
-- NOTE: doc_id is not guaranteed unique in the synthetic dataset,
-- so we use a composite primary key (doc_id, doc_type).
-- ======================
CREATE TABLE IF NOT EXISTS environmental_docs (
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (doc_id, doc_type)
);

-- ======================
-- Main Safety Records Table (Fact Table)
-- ======================
CREATE TABLE IF NOT EXISTS safety_records (
    record_id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    location TEXT,
    work_type TEXT,
    hazard_id TEXT REFERENCES hazards(hazard_id),
    exposure_level TEXT CHECK (
        exposure_level IN ('Low', 'Moderate', 'High', 'Severe')
    ),
    temperature_f INT,
    noise_db INT,
    airborne_particles_ppm DECIMAL(6,2),
    supervisor TEXT,
    shift TEXT CHECK (shift IN ('Day', 'Swing', 'Night')),
    incident_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================
-- Many-to-Many: PPE Assignments
-- ======================
CREATE TABLE IF NOT EXISTS safety_record_ppe (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    ppe_id TEXT REFERENCES ppe(ppe_id),
    PRIMARY KEY (record_id, ppe_id)
);

-- ======================
-- Many-to-Many: Environmental Docs
-- (doc_id, doc_type) references environmental_docs composite key
-- ======================
CREATE TABLE IF NOT EXISTS safety_record_docs (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (record_id, doc_id, doc_type),
    FOREIGN KEY (doc_id, doc_type) REFERENCES environmental_docs(doc_id, doc_type)
);

-- ======================
-- Useful Indexes
-- ======================
CREATE INDEX IF NOT EXISTS idx_safety_date ON safety_records(date);
CREATE INDEX IF NOT EXISTS idx_safety_hazard ON safety_records(hazard_id);
CREATE INDEX IF NOT EXISTS idx_safety_incident ON safety_records(incident_flag);

-- ============================================
-- AUL (Authorized User List) Tables
-- Source: Krystal Tilson, Tinker AFB, March 2026
-- Sheet: "HM - MATERIAL AUTH IN SHOP SEQ"
-- ============================================

-- ======================
-- Materials Reference Table
-- Each MSN (Material Stock Number) identifies a unique hazardous material.
-- Profiling confirmed: msn->noun is 1:1 (1 minor conflict resolved by
-- majority-wins heuristic), msn->bulk_issue is strictly 1:1.
-- ======================
CREATE TABLE IF NOT EXISTS materials (
    msn TEXT PRIMARY KEY,
    noun TEXT NOT NULL,
    bulk_issue BOOLEAN
);

-- ======================
-- Shops Reference Table
-- Each shop_code identifies a location authorized to handle materials.
-- Profiling confirmed: shop_code->org_symbol is strictly 1:1.
-- ======================
CREATE TABLE IF NOT EXISTS shops (
    shop_code TEXT PRIMARY KEY,
    org_symbol TEXT NOT NULL
);

-- ======================
-- Material Authorizations (Fact Table)
-- One row per distinct material-shop-process authorization.
-- dist_pct uses NUMERIC(7,4) to preserve values like 33.3333 without
-- truncation. Values are stored as literal percentages (100 = 100%).
-- ======================
CREATE TABLE IF NOT EXISTS material_authorizations (
    id SERIAL PRIMARY KEY,
    msn TEXT NOT NULL REFERENCES materials(msn),
    shop_code TEXT NOT NULL REFERENCES shops(shop_code),
    process_name TEXT,
    local_process_name TEXT,
    dist_pct NUMERIC(7,4),
    max_on_hand INTEGER
);

CREATE INDEX IF NOT EXISTS idx_matauth_shop_code ON material_authorizations(shop_code);
CREATE INDEX IF NOT EXISTS idx_matauth_msn ON material_authorizations(msn);

-- ============================================
-- AI Assessment + Feedback Logging (MVP)
-- Purpose: persist user feedback on AI responses for future refinement.
-- ============================================

-- Minimal parent record for each AI-generated response returned by /api/v1/analyze-task
CREATE TABLE IF NOT EXISTS ai_assessments (
    assessment_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_description TEXT NOT NULL,
    response_json TEXT NOT NULL
);

-- Feedback submitted from the frontend AI Response box
CREATE TABLE IF NOT EXISTS ai_feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessment_id TEXT NOT NULL REFERENCES ai_assessments(assessment_id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL CHECK (
        feedback_type IN ('thumbs_up', 'thumbs_down', 'report_inaccuracy')
    ),
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_ai_feedback_assessment_id ON ai_feedback(assessment_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_created_at ON ai_feedback(created_at);