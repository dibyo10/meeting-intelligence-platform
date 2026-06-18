"""Application configuration, loaded from environment / .env via pydantic-settings.

Paths are resolved relative to the repo so the app behaves the same regardless of the
working directory it is launched from.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]     # .../meeting-intelligence
BACKEND = Path(__file__).resolve().parents[1]  # .../meeting-intelligence/backend


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- credentials ---
    gemini_api_key: str = ""
    google_api_key: str = ""
    hf_token: str = ""

    # --- models ---
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "gemini-embedding-001"
    gemini_thinking_level: str = "high"

    # --- auth (off until AUTH_PASSWORD is set) ---
    auth_username: str = "admin"
    auth_password: str = ""          # empty => auth disabled, API stays open
    auth_secret: str = ""            # HMAC signing key; falls back to auth_password if empty
    auth_token_ttl_minutes: int = 1440  # 24h

    # --- whisper ---
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # --- rag ---
    embed_dim: int = 768
    rag_top_k: int = 8

    # --- paths / server ---
    data_dir: str = ""
    cors_origins: str = "*"  # permissive by default; set to your frontend URL to restrict

    # ---------- derived ----------
    @property
    def gemini_key(self) -> str:
        return self.gemini_api_key or self.google_api_key

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_key)

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_password)

    @property
    def auth_signing_key(self) -> str:
        return self.auth_secret or self.auth_password

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir) if self.data_dir else (ROOT / "data")
        if not p.is_absolute():
            p = (BACKEND / p).resolve()
        return p

    @property
    def uploads_dir(self) -> Path:
        return self.data_path / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_path / "chroma"

    @property
    def db_path(self) -> Path:
        return self.data_path / "meetings.sqlite3"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
