"""
main.py — FastAPI entry point for the Tinker AFB AI-Based Risk Assessment System.

Run the development server:
    cd api
    source venv/bin/activate
    python3 -m uvicorn main:app --reload --port 8000

Authentication modes (configured via api/.env):
  - No env vars set    → fully open, no credentials required (dev/demo)
  - API_KEY=xxx        → all data routes require the X-API-Key header
  - JWT_SECRET_KEY=xxx → full user login with role-based access (viewer/analyst/supervisor)
  - Both set           → API key is accepted as a supervisor-level override

Interactive API documentation is available at http://localhost:8000/docs when running.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.auth import verify_api_key, require_role
from routers.safety_records import router as safety_records_router
from routers.admin import router as admin_router
from routers.feedback import router as feedback_router
from routers.waste import router as waste_router
from routers.assessments import router as assessments_router
from routers.reference_data import router as reference_data_router
from routers.materials import router as materials_router
from routers.auth_router import router as auth_router
from routers.prediction import router as prediction_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Risk Assessment Database — Tinker AFB",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ── Public endpoints ──────────────────────────────────────────────────────────


@app.get("/api/v1/health")
def health_check():
    """Health check — no auth required so monitoring tools can probe freely."""
    auth_mode = "open"
    if settings.JWT_SECRET_KEY:
        auth_mode = "jwt"
    elif settings.API_KEY:
        auth_mode = "api_key"
    return {"status": "ok", "message": "API online", "version": settings.VERSION, "auth_mode": auth_mode}


# Auth routes (login/refresh/me) — no pre-auth needed
app.include_router(auth_router)

# Admin routes — uses its own internal password check
app.include_router(admin_router)


# ── Protected data routes ─────────────────────────────────────────────────────
# API key guard applies to all data routes.
# Role guard on write operations when JWT is enabled.

_api_key_dep = [Depends(verify_api_key)]

app.include_router(safety_records_router, dependencies=_api_key_dep)
app.include_router(feedback_router, dependencies=_api_key_dep)
app.include_router(waste_router, dependencies=_api_key_dep)
app.include_router(assessments_router, dependencies=_api_key_dep)
app.include_router(reference_data_router, dependencies=_api_key_dep)
app.include_router(materials_router, dependencies=_api_key_dep)
app.include_router(prediction_router, dependencies=_api_key_dep)
