"""
admin.py — Admin Authentication Router

POST /api/v1/admin/login
  Verifies a submitted password against the ADMIN_MASTER_PASSWORD env var.
  Returns { "success": true } on match, raises HTTP 401 on failure.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.config import settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AdminLoginRequest(BaseModel):
    password: str


@router.post("/login")
def admin_login(body: AdminLoginRequest):
    if not settings.ADMIN_MASTER_PASSWORD or body.password != settings.ADMIN_MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return {"success": True}
