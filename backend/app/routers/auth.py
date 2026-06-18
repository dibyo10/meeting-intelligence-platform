"""Authentication endpoints: log in to obtain a token, and inspect the current identity."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from .. import schemas
from ..auth import authenticate, create_token, require_auth
from ..config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest):
    s = get_settings()
    if not s.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled on this server (no AUTH_PASSWORD configured).",
        )
    if not authenticate(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return schemas.TokenResponse(
        access_token=create_token(body.username),
        expires_in=s.auth_token_ttl_minutes * 60,
    )


@router.get("/me", response_model=schemas.IdentityResponse)
def me(identity: str = Depends(require_auth)):
    return schemas.IdentityResponse(
        username=identity, auth_enabled=get_settings().auth_enabled
    )
