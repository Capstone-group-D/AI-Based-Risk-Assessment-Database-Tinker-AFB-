# AI-Based Risk Assessment Database — Tinker AFB

An AI-powered industrial risk assessment system for depot maintenance facilities at Tinker AFB. The system centralizes safety records, analyzes plain-language task descriptions using NLP to identify hazards, recommends PPE and engineering controls based on historical data (including mandatory Tinker AFB procedural controls), and surfaces analytics for incident trends and compliance posture. It also exposes the AUL (Authorized User List) material authorization data, searchable by material name, MSN, or shop code.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1 — Backend

```bash
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
cd ../db && python3 init_db.py
cd ../api && python3 -m uvicorn main:app --reload --port 8000
```

### 2 — Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — both servers must be running simultaneously.

> For full setup instructions, Docker deployment, environment variables, and troubleshooting, see [**Getting Started →**](./docs/02_getting_started.md)

---

## Documentation

| Document | Description |
|---|---|
| [01 — Project Overview](./docs/01_overview.md) | What the system does, architecture, technology stack |
| [02 — Getting Started](./docs/02_getting_started.md) | Full setup guide, environment variables, Docker, troubleshooting |
| [03 — Feature Reference](./docs/03_features.md) | Every page and feature explained for end users |
| [04 — API Reference](./docs/04_api_reference.md) | All endpoints: methods, auth, request/response formats |
| [05 — Database Schema](./docs/05_database_schema.md) | Every table and column documented, SQLite vs PostgreSQL notes |
| [06 — AI / NLP Engine](./docs/06_nlp_and_ai_engine.md) | How the task analysis works, accuracy notes, control rule tables |
| [07 — Future Improvements](./docs/07_future_improvements.md) | Roadmap: PostgreSQL migration, model upgrades, user management, and more |

---

## Technology Stack

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

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check — no auth required |
| GET | `/api/v1/safety-records` | List all safety records |
| POST | `/api/v1/safety-records` | Create new safety record (supervisor role) |
| GET | `/api/v1/safety-records/export` | Download records as CSV |
| POST | `/api/recommend-ppe` | Direct PPE recommendation by hazard/process |
| POST | `/api/v1/analyze-task` | NLP task → PPE recommendation (analyst role) |
| POST | `/api/v1/ai-feedback` | Submit feedback on AI result |
| GET | `/api/v1/ai-assessments` | List AI assessment history |
| GET | `/api/v1/ai-assessments/{id}/report` | Print-ready HTML report |
| GET | `/api/v1/ppe` | PPE reference catalog |
| GET | `/api/v1/hazards` | Hazard reference catalog |
| GET | `/api/v1/materials` | AUL materials (searchable by name, MSN, or shop code) |
| GET | `/api/v1/materials/{msn}/authorizations` | Shop authorizations for a material |
| GET | `/api/v1/shops` | AUL shop list |
| POST | `/api/v1/materials/recommend-ppe` | PPE recommendation for an AUL material |
| GET | `/api/v1/predict-risk` | Weighted risk score + trend analysis |

Interactive docs: **http://localhost:8000/docs**

---

## Running Tests

```bash
# Python (from repo root, venv active)
pytest tests/python -v

# JavaScript
cd tests/javascript && npm install && npm test
```

---

## Running with Docker

```bash
docker-compose up --build
# Frontend: http://localhost:3000  |  Backend: http://localhost:8000
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branching strategy, code style (Black/Flake8), and PR guidelines.
