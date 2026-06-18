"""Simple, dependency-free authentication.

Design goals (deliberately minimal):
* **One admin account** read from the environment (``AUTH_USERNAME`` / ``AUTH_PASSWORD``).
  No users table, no registration flow — the env IS the secret.
* **Stateless tokens** signed with HMAC-SHA256 using only the Python standard library, so
  there are no extra runtime dependencies (no JWT/bcrypt packages to install or pin).
* **Off until configured.** If ``AUTH_PASSWORD`` is empty the whole API stays open exactly
  as before — so existing clients (and the frontend) keep working until auth is switched on
  by setting the env vars. When it *is* set, every data route requires a valid token.

Token format:  ``<base64url(payload-json)>.<base64url(hmac-sha256)>``
where payload is ``{"sub": <username>, "exp": <unix-seconds>}``.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings

logger = logging.getLogger(__name__)

# auto_error=False so we can return our own 401 (and allow the open mode to skip auth).
_bearer = HTTPBearer(auto_error=False)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(payload_b64: str, key: str) -> str:
    sig = hmac.new(key.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(sig)


def create_token(username: str, ttl_minutes: Optional[int] = None) -> str:
    """Issue a signed token for ``username`` valid for ``ttl_minutes``."""
    s = get_settings()
    ttl = ttl_minutes if ttl_minutes is not None else s.auth_token_ttl_minutes
    payload = {"sub": username, "exp": int(time.time()) + ttl * 60}
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64, s.auth_signing_key)}"


def verify_token(token: str) -> str:
    """Return the username encoded in a valid token, else raise ``ValueError``."""
    s = get_settings()
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        raise ValueError("malformed token")
    expected = _sign(payload_b64, s.auth_signing_key)
    if not hmac.compare_digest(expected, sig):
        raise ValueError("bad signature")
    try:
        payload = json.loads(_b64decode(payload_b64))
    except Exception:
        raise ValueError("unreadable payload")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expired")
    sub = payload.get("sub")
    if not sub:
        raise ValueError("no subject")
    return str(sub)


def authenticate(username: str, password: str) -> bool:
    """Constant-time check of a username/password pair against the configured admin."""
    s = get_settings()
    if not s.auth_enabled:
        return False
    user_ok = hmac.compare_digest(username or "", s.auth_username)
    pass_ok = hmac.compare_digest(password or "", s.auth_password)
    return user_ok and pass_ok


def require_auth(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """FastAPI dependency guarding protected routes.

    * Auth disabled (no ``AUTH_PASSWORD``)  -> returns ``"anonymous"`` (open mode).
    * Auth enabled + valid Bearer token     -> returns the username.
    * Auth enabled + missing/invalid token  -> 401.
    """
    s = get_settings()
    if not s.auth_enabled:
        return "anonymous"
    if creds is None or (creds.scheme or "").lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verify_token(creds.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
