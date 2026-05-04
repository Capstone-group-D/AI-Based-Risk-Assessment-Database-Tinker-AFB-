"""
main.py — FastAPI Backend for AI-Based Risk Assessment Database

Tinker AFB PPE Recommendation Engine — Sprint 2 API

Run with:
  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers.safety_records import router as safety_records_router
from routers.feedback import router as feedback_router
from routers.waste import router as waste_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Risk Assessment Database — Tinker AFB",
    version=settings.VERSION,
)

# CORS — allow the Vite dev server (port 3000) to call this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(safety_records_router)
app.include_router(feedback_router)
app.include_router(waste_router)
