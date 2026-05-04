"""
auth.py — Authentication & Authorization

Supports two complementary auth mechanisms:

1. API Key (X-API-Key header) — simple shared-secret for machine-to-machine or
   quick deployments. Enabled when API_KEY is set in the environment.

2. JWT Bearer tokens — full user-based auth with roles.
   POST /api/v1/auth/login  → returns access token + refresh token
   POST /api/v1/auth/refresh → rotates access token using refresh token
   GET  /api/v1/auth/me      → returns current user info

   Roles (least → most privileged):
     viewer     — read-only (GET endpoints only)
     analyst    — read + AI analysis + feedback
     supervisor — full access including writing safety records

   When JWT_SECRET_KEY is not set (default), JWT auth is disabled and all
   routes are open — same as the legacy API key pass-through behaviour.

Seeded default users (change passwords in production):
  admin / admin123   (role: supervisor)
  analyst / analyst123 (role: analyst)
  viewer / viewer123   (role: viewer)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from passlib.context import CryptContext

from core.config import settings

try:
    from jose import JWTError, jwt as jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

ROLE_HIERARCHY = {"viewer": 0, "analyst": 1, "supervisor": 2}

# ── Password hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── In-memory user store (replace with DB table in production) ────────────────

_USERS = {
    "admin": {
        "user_id": str(uuid.uuid4()),
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "supervisor",
        "full_name": "System Administrator",
    },
    "analyst": {
        "user_id": str(uuid.uuid4()),
        "username": "analyst",
        "hashed_password": hash_password("analyst123"),
        "role": "analyst",
        "full_name": "Safety Analyst",
    },
    "viewer": {
        "user_id": str(uuid.uuid4()),
        "username": "viewer",
        "hashed_password": hash_password("viewer123"),
        "role": "viewer",
        "full_name": "Read-Only Viewer",
    },
}


def get_user(username: str) -> Optional[dict]:
    return _USERS.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


# ── Token helpers ─────────────────────────────────────────────────────────────

def _create_token(data: dict, expires_delta: timedelta) -> str:
    if not _JOSE_AVAILABLE or not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT not configured")
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jose_jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user: dict) -> str:
    return _create_token(
        {"sub": user["username"], "role": user["role"], "uid": user["user_id"], "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user: dict) -> str:
    return _create_token(
        {"sub": user["username"], "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    if not _JOSE_AVAILABLE or not settings.JWT_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT not configured")
    try:
        return jose_jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )


# ── FastAPI security schemes ──────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_current_user_from_bearer(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> Optional[dict]:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected an access token")
    user = get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def verify_api_key(
    api_key: Optional[str] = Security(_api_key_header),
) -> None:
    """Legacy API key guard — pass-through when API_KEY is not configured."""
    if not settings.API_KEY:
        return
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide the X-API-Key request header.",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    api_key: Optional[str] = Security(_api_key_header),
) -> Optional[dict]:
    """
    Returns the current authenticated user, or None if JWT is not configured
    (open / API-key-only mode).

    Raises 401 if JWT IS configured and the token is missing/invalid.
    """
    if not settings.JWT_SECRET_KEY:
        return None  # auth disabled
    if api_key and settings.API_KEY and api_key == settings.API_KEY:
        # API key override — treat as supervisor
        return {"username": "api_key_user", "role": "supervisor", "full_name": "API Key"}
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token or X-API-Key header.",
        )
    return _get_current_user_from_bearer(credentials)


def require_role(minimum_role: str):
    """
    Returns a FastAPI dependency that enforces a minimum role.

    Usage:
        @router.post("/...", dependencies=[Depends(require_role("supervisor"))])
    """
    def _check(user: Optional[dict] = Depends(get_current_user)):
        if user is None:
            return  # JWT disabled, open access
        user_level = ROLE_HIERARCHY.get(user["role"], -1)
        required_level = ROLE_HIERARCHY.get(minimum_role, 999)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {minimum_role}.",
            )
    return _check
