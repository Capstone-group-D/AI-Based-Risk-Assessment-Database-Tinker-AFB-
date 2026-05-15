# Getting Started — Running the Application

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or newer | `python3 --version` |
| Node.js | 18 or newer | `node --version` |
| npm | 9 or newer | Included with Node.js |
| Docker *(optional)* | 24+ | For containerized production deployment |

---

## Option A — Local Development (Recommended for First Run)

Both the backend API and the frontend must run simultaneously. Open two separate terminal windows.

### Step 1 — Set Up the Backend

```bash
# Navigate to the api directory
cd api

# Create a Python virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install production dependencies
pip install -r requirements.txt

# Install the spaCy English language model (required for NLP task analysis)
python3 -m spacy download en_core_web_sm
```

### Step 2 — Initialize the Database

```bash
# From the repo root (one directory up from api/)
cd ..

python3 db/init_db.py
```

This creates `risk_assessment.db` at the repo root, applies the full schema, and inserts seed data (hazard catalog, PPE catalog, waste categories, and sample safety records).

**If you have the AUL CSV file** (`aul_mxsg_2026-03-03.csv`), place it at `db/seed_data/aul_mxsg_2026-03-03.csv` before running `init_db.py`. It will automatically import 11,000+ materials, 354 shops, and 26,000+ shop authorizations.

### Step 3 — Start the Backend

```bash
cd api
source venv/bin/activate    # if not already active
python3 -m uvicorn main:app --reload --port 8000
```

The API is now available at:
- **API base**: http://localhost:8000
- **Interactive docs (Swagger UI)**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/v1/health

### Step 4 — Set Up and Start the Frontend

In a **second terminal window**:

```bash
cd frontend
npm install
npm run dev
```

The app is now available at **http://localhost:3000**.

The Vite dev server automatically proxies all `/api/*` requests to `http://localhost:8000`, so the frontend and backend communicate seamlessly.

---

## Option B — Docker Compose (Production / Demo)

Docker Compose starts both services with a single command. No separate terminals needed.

```bash
# From the repo root
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

To run with an API key (recommended for shared/demo deployments):

```bash
API_KEY=your-secret-key docker-compose up --build
```

---

## Environment Variables

All environment variables are optional. The app runs in open/dev mode with no configuration.

Create `api/.env` (copy from `api/.env.example`) to override defaults:

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `"Tinker AFB AI Risk Assessment System"` | Displayed in API docs |
| `VERSION` | `"0.4.0"` | API version label |
| `DATABASE_URL` | `""` | Leave blank for SQLite. Set to a PostgreSQL URI for production. |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `API_KEY` | `""` | If set, all data routes require `X-API-Key: <value>` header |
| `JWT_SECRET_KEY` | `""` | If set, enables full JWT user auth with roles |
| `ADMIN_MASTER_PASSWORD` | `""` | Password for the admin panel unlock in the frontend |

Create `frontend/.env` to configure the frontend:

| Variable | Default | Description |
|---|---|---|
| `VITE_API_KEY` | `""` | Must match `API_KEY` in `api/.env` |

---

## Authentication Modes

The system supports three modes, selected automatically based on which environment variables are set:

| Mode | How to Enable | Who Can Access |
|---|---|---|
| **Open** (dev/demo) | Leave `API_KEY` and `JWT_SECRET_KEY` blank | Everyone — no credentials required |
| **API Key** | Set `API_KEY` in `api/.env` and `VITE_API_KEY` in `frontend/.env` | Anyone with the key |
| **JWT / Roles** | Set `JWT_SECRET_KEY` in `api/.env` | Users must log in; roles control write access |

With JWT enabled, the login screen appears automatically. Users are configured in `api/core/auth.py` in the `USERS` dictionary.

---

## Running Tests

### Python (pytest)

```bash
# From the repo root, with the virtual environment active
cd api
source venv/bin/activate
cd ..
pytest tests/python -v
```

> **Known issue:** On Python 3.12, `test_api_integration.py` and `test_recommend_ppe_endpoint.py` fail at collection time with a `ValueError` from the `passlib` library related to bcrypt password length. This is a pre-existing incompatibility between passlib 1.7.x and Python 3.12 and does not affect the running application. All other tests pass. To run only the passing tests:
> ```bash
> pytest tests/python -v --ignore=tests/python/test_api_integration.py --ignore=tests/python/test_recommend_ppe_endpoint.py
> ```


### JavaScript (Jest)

```bash
cd tests/javascript
npm install
npm test
```

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Address already in use` on port 8000 | Another process (or a previous run) is using port 8000 | Kill the other process: `lsof -i :8000` then `kill -9 <PID>` |
| `ModuleNotFoundError: No module named 'spacy'` | Virtual environment not activated | Run `source venv/bin/activate` first |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | spaCy model not downloaded | Run `python3 -m spacy download en_core_web_sm` |
| Frontend shows "Could not reach the API" | Backend not running | Start `uvicorn` in a separate terminal first |
| `No AUL data available` in PPE Guide | AUL CSV was not present during `init_db.py` | Place CSV at `db/seed_data/aul_mxsg_2026-03-03.csv` and rerun `python3 db/init_db.py` |
