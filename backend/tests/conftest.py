"""Shared pytest setup.

The environment is configured *before* the app is imported so that the database points at
a throwaway directory and auth starts disabled. Individual tests opt into auth with the
``auth_on`` fixture, which flips the env vars and clears the settings cache (``require_auth``
and the login route read settings live, so this takes effect immediately).
"""
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Isolated data dir (fresh sqlite + chroma) so tests never touch real data.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="mip-tests-")
# Start with auth OFF.
for _k in ("AUTH_USERNAME", "AUTH_PASSWORD", "AUTH_SECRET", "AUTH_TOKEN_TTL_MINUTES"):
    os.environ.pop(_k, None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_on():
    """Turn auth ON (admin / secret123) for the duration of a test."""
    creds = {"username": "admin", "password": "secret123"}
    os.environ["AUTH_USERNAME"] = creds["username"]
    os.environ["AUTH_PASSWORD"] = creds["password"]
    os.environ["AUTH_SECRET"] = "unit-test-signing-key"
    get_settings.cache_clear()
    try:
        yield creds
    finally:
        for k in ("AUTH_USERNAME", "AUTH_PASSWORD", "AUTH_SECRET"):
            os.environ.pop(k, None)
        get_settings.cache_clear()
