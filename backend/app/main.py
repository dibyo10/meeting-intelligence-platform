"""FastAPI application entrypoint for the AI Meeting Intelligence Platform."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import action_items, analytics, meetings, search, speakers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()

app = FastAPI(
    title="AI Meeting Intelligence Platform",
    description="Audio → transcript → diarisation → summary → action items → searchable RAG archive.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "model": settings.gemini_model,
        "embed_model": settings.gemini_embed_model,
        "gemini_configured": settings.has_gemini,
        "diarisation_configured": bool(settings.hf_token),
        "whisper_model": settings.whisper_model,
    }


app.include_router(meetings.router)
app.include_router(speakers.router)
app.include_router(action_items.router)
app.include_router(search.router)
app.include_router(analytics.router)
