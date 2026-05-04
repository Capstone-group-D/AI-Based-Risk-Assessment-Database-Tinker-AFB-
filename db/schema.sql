-- ============================================
-- AI Safety Risk Assessment Database Schema
-- ============================================
 

-- Hazards Reference Table

CREATE TABLE IF NOT EXISTS hazards (
    hazard_id TEXT PRIMARY KEY,
    hazard_label TEXT NOT NULL,
    hazard_category TEXT NOT NULL
);


-- PPE Reference Table

CREATE TABLE IF NOT EXISTS ppe (
    ppe_id TEXT PRIMARY KEY,
    ppe_label TEXT NOT NULL,
    ppe_category TEXT NOT NULL
);


-- Environmental Documentation

CREATE TABLE IF NOT EXISTS environmental_docs (
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (doc_id, doc_type)
);


-- Main Safety Records Table (Fact Table)

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


-- Many-to-Many: PPE Assignments

CREATE TABLE IF NOT EXISTS safety_record_ppe (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    ppe_id TEXT REFERENCES ppe(ppe_id),
    PRIMARY KEY (record_id, ppe_id)
);


-- Many-to-Many: Environmental Docs

CREATE TABLE IF NOT EXISTS safety_record_docs (
    record_id TEXT REFERENCES safety_records(record_id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    PRIMARY KEY (record_id, doc_id, doc_type),
    FOREIGN KEY (doc_id, doc_type) REFERENCES environmental_docs(doc_id, doc_type)
);


CREATE INDEX IF NOT EXISTS idx_safety_date ON safety_records(date);
CREATE INDEX IF NOT EXISTS idx_safety_hazard ON safety_records(hazard_id);
CREATE INDEX IF NOT EXISTS idx_safety_incident ON safety_records(incident_flag);

-- ============================================
-- AUL Tables
-- ============================================


-- Materials Reference Table

CREATE TABLE IF NOT EXISTS materials (
    msn TEXT PRIMARY KEY,
    noun TEXT NOT NULL,
    bulk_issue BOOLEAN
);


-- Shops Reference Table
-- Each shop_code identifies a location authorized to handle materials.

CREATE TABLE IF NOT EXISTS shops (
    shop_code TEXT PRIMARY KEY,
    org_symbol TEXT NOT NULL
);


-- Material Authorizations (Fact Table)
-- One row per distinct material-shop-process authorization.
-- dist_pct uses NUMERIC(7,4) to preserve values like 33.3333 without
-- truncation. Values are stored as literal percentages (100 = 100%).

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


-- AI Assessment + Feedback Logging
-- Purpose: persist user feedback on AI responses for future refinement.


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

-- ============================================
-- Hazardous Waste and Recycling Tracking
-- ============================================


-- Waste Categories Reference Table

CREATE TABLE IF NOT EXISTS waste_categories (
    waste_category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    hazard_class TEXT NOT NULL, -- e.g., 'Corrosive', 'Flammable', 'Toxic'
    disposal_method TEXT NOT NULL, -- e.g., 'Incineration', 'Landfill', 'Recycling'
    epa_code TEXT -- EPA waste code if applicable
);


-- Waste Records Table

CREATE TABLE IF NOT EXISTS waste_records (
    waste_record_id TEXT PRIMARY KEY,
    date_generated DATE NOT NULL,
    location TEXT NOT NULL, -- Depot/shop location
    waste_category_id TEXT NOT NULL REFERENCES waste_categories(waste_category_id),
    quantity_kg DECIMAL(10,2) NOT NULL,
    quantity_unit TEXT DEFAULT 'kg',
    generator_name TEXT, -- Person/department generating the waste
    process_type TEXT, -- e.g., 'Engine Wash', 'Paint Stripping', 'Parts Cleaning'
    container_type TEXT, -- e.g., '55-gallon drum', '5-gallon pail'
    storage_location TEXT,
    disposal_date DATE,
    disposal_method TEXT,
    recycler_name TEXT, -- If recycled
    cost_usd DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Recycling Opportunities Table

CREATE TABLE IF NOT EXISTS recycling_opportunities (
    opportunity_id TEXT PRIMARY KEY,
    waste_category_id TEXT NOT NULL REFERENCES waste_categories(waste_category_id),
    opportunity_name TEXT NOT NULL,
    description TEXT NOT NULL,
    recycler_contact TEXT,
    estimated_value_per_kg DECIMAL(8,2), -- Economic value of recycling
    environmental_impact TEXT, -- Environmental benefits
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Pollution Prevention Opportunities Table

CREATE TABLE IF NOT EXISTS pollution_prevention_opportunities (
    opportunity_id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL, -- e.g., 'Engine Wash', 'Aircraft Painting'
    task_description TEXT NOT NULL,
    waste_category_id TEXT REFERENCES waste_categories(waste_category_id),
    prevention_method TEXT NOT NULL, -- e.g., 'Use biodegradable solvents', 'Implement closed-loop system'
    expected_reduction_percent DECIMAL(5,2), -- Expected waste reduction percentage
    implementation_cost_usd DECIMAL(10,2),
    payback_period_months INTEGER,
    priority_level TEXT CHECK (priority_level IN ('Low', 'Medium', 'High', 'Critical')),
    responsible_party TEXT, -- Who implements this
    status TEXT DEFAULT 'Identified' CHECK (status IN ('Identified', 'Planned', 'Implementing', 'Completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Task-Waste Relationships

CREATE TABLE IF NOT EXISTS task_waste_relationships (
    task_name TEXT NOT NULL,
    waste_category_id TEXT NOT NULL REFERENCES waste_categories(waste_category_id),
    average_quantity_kg DECIMAL(8,2),
    frequency TEXT, -- e.g., 'Daily', 'Weekly', 'Monthly'
    PRIMARY KEY (task_name, waste_category_id)
);


-- Indexes for Waste Management

CREATE INDEX IF NOT EXISTS idx_waste_date ON waste_records(date_generated);
CREATE INDEX IF NOT EXISTS idx_waste_location ON waste_records(location);
CREATE INDEX IF NOT EXISTS idx_waste_category ON waste_records(waste_category_id);
CREATE INDEX IF NOT EXISTS idx_waste_disposal ON waste_records(disposal_date);
CREATE INDEX IF NOT EXISTS idx_prevention_task ON pollution_prevention_opportunities(task_name);
CREATE INDEX IF NOT EXISTS idx_prevention_priority ON pollution_prevention_opportunities(priority_level);
CREATE INDEX IF NOT EXISTS idx_prevention_status ON pollution_prevention_opportunities(status);