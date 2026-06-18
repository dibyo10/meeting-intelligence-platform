"""Auth unit tests: token signing/verification and credential checks."""
import pytest

from app import auth
from app.config import get_settings


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secret123")
    monkeypatch.setenv("AUTH_SECRET", "sign-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_token_roundtrip(enabled):
    token = auth.create_token("admin")
    assert auth.verify_token(token) == "admin"


def test_token_tampered_signature(enabled):
    token = auth.create_token("admin")
    payload, sig = token.split(".", 1)
    tampered = f"{payload}.{sig[:-2]}xy"
    with pytest.raises(ValueError):
        auth.verify_token(tampered)


def test_token_expired(enabled):
    token = auth.create_token("admin", ttl_minutes=-1)
    with pytest.raises(ValueError):
        auth.verify_token(token)


def test_token_wrong_secret_rejected(enabled, monkeypatch):
    token = auth.create_token("admin")
    monkeypatch.setenv("AUTH_SECRET", "different-key")
    get_settings.cache_clear()
    with pytest.raises(ValueError):
        auth.verify_token(token)


def test_authenticate(enabled):
    assert auth.authenticate("admin", "secret123") is True
    assert auth.authenticate("admin", "wrong") is False
    assert auth.authenticate("intruder", "secret123") is False


def test_authenticate_false_when_disabled(monkeypatch):
    monkeypatch.delenv("AUTH_PASSWORD", raising=False)
    get_settings.cache_clear()
    assert auth.authenticate("admin", "secret123") is False
    get_settings.cache_clear()
