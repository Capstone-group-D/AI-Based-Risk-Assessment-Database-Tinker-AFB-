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