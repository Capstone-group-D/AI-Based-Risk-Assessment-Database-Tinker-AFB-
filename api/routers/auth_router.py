"""
auth_router.py — Login, Token Refresh, and User Info Endpoints

These endpoints are unauthenticated themselves (they ARE the auth entry points).

POST /api/v1/auth/login    — exchange username+password for JWT tokens
POST /api/v1/auth/refresh  — exchange refresh token for new access token
GET  /api/v1/auth/me       — return current user details
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user,
    get_current_user,
)
from core.config import settings
from schemas import TokenResponse, TokenRefreshRequest, UserInfo

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Exchange username + password for an access token and a refresh token.
    Uses standard OAuth2 password flow form data (application/x-www-form-urlencoded).
    """
    if not settings.JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="JWT authentication is not enabled. Set JWT_SECRET_KEY in your environment.",
        )

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        token_type="bearer",
        role=user["role"],
        username=user["username"],
        full_name=user["full_name"],
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: TokenRefreshRequest):
    """Exchange a valid refresh token for a new access token."""
    if not settings.JWT_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="JWT not enabled")

    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected a refresh token")

    user = get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        token_type="bearer",
        role=user["role"],
        username=user["username"],
        full_name=user["full_name"],
    )


@router.get("/me", response_model=UserInfo)
def get_me(current_user: Optional[dict] = Depends(get_current_user)):
    """Returns info about the currently authenticated user."""
    if not settings.JWT_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="JWT not enabled")
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return UserInfo(
        username=current_user["username"],
        full_name=current_user.get("full_name", ""),
        role=current_user["role"],
    )
