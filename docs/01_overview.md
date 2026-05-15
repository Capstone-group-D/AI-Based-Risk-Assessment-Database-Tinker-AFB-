# Tinker AFB AI-Based Risk Assessment System — Project Overview

## What This System Does

The AI-Based Risk Assessment Database is a web application built for Tinker Air Force Base depot maintenance facilities. Its purpose is to replace paper-based and spreadsheet-based safety processes with a centralized, intelligent system that:

- **Analyzes work tasks in plain English** — type a description of a task, and the AI engine identifies the associated hazards and recommends the required personal protective equipment (PPE) and engineering controls.
- **Surfaces Tinker AFB-specific procedural controls** — recommendations include mandatory procedures directly sourced from the Tinker AFB Risk Assessment Form (Form 493, confined space permits, hot work fire watch, etc.).
- **Centralizes safety records** — all safety records, incident flags, exposure levels, and associated PPE assignments are stored in a queryable database.
- **Tracks AI assessment history** — every AI-generated recommendation is stored so supervisors can review and audit past analyses.
- **Provides analytics and risk prediction** — dashboards show incident trends, top hazard categories, and a weighted risk score derived from historical safety record data.
- **Exposes AUL material data** — the Authorized User List (AUL) of hazardous materials is searchable by material name, MSN, or shop code, and links directly into the PPE recommendation engine.
- **Tracks hazardous waste** — waste generation records, recycling opportunities, and pollution prevention initiatives are logged and visible.

---

## Who This Is For

| Role | How They Use the System |
|---|---|
| **Safety Technician** | Enters task descriptions to get PPE recommendations before starting work |
| **Supervisor** | Reviews AI assessment history, logs official safety records, monitors analytics |
| **Industrial Hygienist** | Reviews AUL materials by shop code, checks PPE recommendations for specific chemicals |
| **Environmental Officer** | Tracks waste generation, monitors pollution prevention initiatives |
| **IT / System Administrator** | Deploys and maintains the application, manages user accounts |

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│               User's Browser                │
│          React 19 + Vite Frontend           │
│         http://localhost:3000               │
└────────────────────┬────────────────────────┘
                     │  HTTP  /api/v1/*
                     │  (proxied by Vite dev server)
┌────────────────────▼────────────────────────┐
│           FastAPI Backend (Python)          │
│         http://localhost:8000               │
│                                             │
│  Routers: safety_records, assessments,      │
│  materials, reference_data, feedback,       │
│  waste, prediction, auth                   │
│                                             │
│  NLP Engine: spaCy + thefuzz               │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│         SQLite Database (dev/demo)          │
│         risk_assessment.db                 │
│                                             │
│  Tables: safety_records, hazards, ppe,      │
│  materials, shops, material_authorizations, │
│  ai_assessments, ai_feedback,               │
│  waste_records, waste_categories, ...       │
└─────────────────────────────────────────────┘
```

For production deployment, the SQLite database is replaced with PostgreSQL (the schema is compatible — see [Future Improvements](./07_future_improvements.md)).

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend framework | React | 19 |
| Frontend build tool | Vite | 7 |
| Charts | Chart.js | Bundled via npm |
| Backend framework | FastAPI | Python 3.10+ |
| Backend server | Uvicorn | — |
| Database | SQLite (dev) / PostgreSQL (prod) | — |
| NLP | spaCy `en_core_web_sm` | 3.8 |
| Fuzzy matching | thefuzz | — |
| Authentication | JWT (python-jose) + API Key | — |
| Containerization | Docker + Docker Compose | — |
| CI | GitHub Actions | — |
| Python testing | pytest | — |
| JavaScript testing | Jest | — |

---

## Repository Structure

```
/api                    FastAPI service
  /core                 App configuration and authentication
    config.py           Settings loaded from .env
    auth.py             API key verification + JWT role enforcement
  /db                   SQLite session helper
  /nlp                  NLP task analyzer (spaCy + fuzzy match)
    analyzer.py
  /routers              One file per endpoint group
    safety_records.py   Safety records CRUD + PPE recommendation engine
    assessments.py      AI assessment history
    materials.py        AUL materials + shop authorizations
    reference_data.py   PPE and hazard catalogs
    feedback.py         AI feedback submission
    waste.py            Hazardous waste tracking
    prediction.py       Risk score calculation
    auth_router.py      Login / token refresh / user info
    admin.py            Admin panel unlock
  main.py               FastAPI app factory + router registration
  schemas.py            All Pydantic request/response models
  requirements.txt      Production Python dependencies
  requirements-dev.txt  Development/test Python dependencies
  .env.example          Environment variable template

/db                     Database layer
  schema.sql            Complete DDL for all tables and indexes
  seed_data.sql         Reference data (hazards, PPE, waste categories)
  init_db.py            Database initialization script (run once)
  import_aul.py         AUL CSV import script
  /seed_data            CSV files for initial data population

/frontend               React + Vite application
  /src
    /api                Axios client + API helper functions
    /components         Page components (one file per page + CSS)
  vite.config.js        Dev server + API proxy configuration
  package.json

/tests
  /python               pytest unit and integration tests
  /javascript           Jest API client tests
  /java                 JUnit stub (not implemented)

/docs                   This documentation directory
docker-compose.yml      Production container configuration
```
