# AI-Based Risk Assessment Database — Tinker AFB

## Project Overview

An AI-powered industrial risk assessment system for depot maintenance facilities at Tinker AFB. The system centralizes safety records, analyzes plain-language task descriptions using NLP to identify hazards, recommends PPE and engineering controls based on historical data, and surfaces analytics for incident trends and compliance posture. It also exposes the AUL (Authorized User List) material authorization data for hazardous materials used across shops.

---

## Technologies

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.10+) |
| Database | SQLite (dev/demo) — schema is PostgreSQL-compatible |
| NLP | spaCy `en_core_web_sm` + thefuzz fuzzy matching |
| Frontend | React 19 + Vite |
| Charts | Chart.js (bundled via npm) |
| Tests | pytest (Python), Jest (JavaScript) |
| CI | GitHub Actions |

---

## Repository Structure

```
/api                  FastAPI service
  /core               Config + auth (API key guard)
  /db                 SQLite session helper
  /nlp                NLP task analyzer (spaCy + fuzzy match)
  /routers            Endpoint modules
/db                   Schema DDL, seed data, DB init script
  /seed_data          seed_data.sql + AUL CSV (if available)
/frontend             React + Vite app
  /src
    /api              Axios client + API helper functions
    /components       Page components (Dashboard, Analytics, etc.)
/tests
  /python             pytest unit + HTTP integration tests
  /javascript         Jest API client tests
  /java               JUnit tests (stub — see Contributing)
.github/workflows     CI (lint + test + build on every PR)
```

---

## Sprint Progress

### Sprint 1 — Domain + Foundations ✅
- Hazard/PPE data fields confirmed
- Database schema drafted (PostgreSQL DDL, SQLite-adapted for dev)
- PPE Recommendation MVP rules defined
- API skeleton + health endpoint

### Sprint 2 — MVP Build ✅
- `POST /api/recommend-ppe` — rule-based PPE + engineering controls
- `POST /api/v1/analyze-task` — NLP → PPE recommendation pipeline
- `POST /api/v1/ai-feedback` — thumbs up/down/report_inaccuracy
- React Dashboard + Analytics frontend
- Python unit tests + GitHub Actions CI

### Sprint 3 — Intelligence Layer + UX ✅
- `GET /api/v1/ai-assessments` — assessment history
- `POST /api/v1/safety-records` — log new records (feeds AI engine)
- `GET /api/v1/ppe` + `GET /api/v1/hazards` — reference catalogs
- `GET /api/v1/materials` + shop authorizations (AUL data)
- AUL material MSN search wired into PPE recommendation engine
- Risk Assessments page (history + log record modal)
- PPE Guide page (3-tab reference: PPE catalog, hazards, AUL materials)
- Optional API key authentication (`X-API-Key` header)
- Chart.js bundled (no CDN dependency)
- Docker + docker-compose for production deployment
- HTTP-layer integration tests (TestClient)

---

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- (Optional) Docker + Docker Compose for containerized deployment

---

### Backend (FastAPI + SQLite)

```bash
cd api

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download the spaCy English language model (required for NLP)
python3 -m spacy download en_core_web_sm

# Initialize the SQLite database with schema + seed data
cd ../db
python3 init_db.py
cd ../api

# Start the development server
python3 -m uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

#### Environment variables (optional)

Create `api/.env` to override defaults:

```
API_KEY=your-secret-key        # Enable X-API-Key auth (leave blank for dev)
```

#### Seeding AUL data

If you have the AUL CSV (`aul_mxsg_2026-03-03.csv`), place it at:

```
db/seed_data/aul_mxsg_2026-03-03.csv
```

Then re-run `python3 db/init_db.py` — it will automatically import materials, shops, and authorizations.

---

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — the Vite dev server proxies all `/api/*` requests to the FastAPI backend.

> Both servers must be running simultaneously for the frontend to connect to the API.

#### Frontend environment variables (optional)

Create `frontend/.env` to override defaults:

```
VITE_API_KEY=your-secret-key   # Must match API_KEY in api/.env
```

---

### Running with Docker (Production)

```bash
# Build and start both containers
docker-compose up --build

# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
```

To set an API key in Docker:

```bash
API_KEY=your-secret-key docker-compose up --build
```

---

### Running Tests

#### Python (pytest)

```bash
# From repo root
cd api
pip install -r requirements-dev.txt
python3 -m spacy download en_core_web_sm
cd ..
pytest tests/python -v
```

#### JavaScript (Jest)

```bash
cd tests/javascript
npm install
npm test
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/safety-records` | List all safety records |
| GET | `/api/v1/safety-records/{id}` | Get single safety record |
| POST | `/api/v1/safety-records` | Create new safety record |
| POST | `/api/recommend-ppe` | Direct PPE recommendation |
| POST | `/api/v1/analyze-task` | NLP task → PPE recommendation |
| POST | `/api/v1/ai-feedback` | Submit feedback on AI result |
| GET | `/api/v1/ai-assessments` | List AI assessment history |
| GET | `/api/v1/ai-assessments/{id}` | Get assessment detail |
| GET | `/api/v1/ppe` | PPE reference catalog |
| GET | `/api/v1/hazards` | Hazard reference catalog |
| GET | `/api/v1/materials` | AUL materials (searchable) |
| GET | `/api/v1/materials/{msn}/authorizations` | Shop authorizations for material |
| GET | `/api/v1/shops` | AUL shop list |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branching strategy, code style (Black/Flake8), and PR guidelines.
