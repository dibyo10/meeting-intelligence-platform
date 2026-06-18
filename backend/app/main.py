"""FastAPI application entrypoint for the AI Meeting Intelligence Platform."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_auth
from .config import get_settings
from .database import init_db, recover_interrupted_meetings
from .routers import action_items, analytics, auth, meetings, search, speakers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    n = recover_interrupted_meetings()
    if n:
        logger.warning("Marked %s meeting(s) interrupted by a previous restart as errored", n)
    if settings.auth_enabled:
        logger.info("Authentication ENABLED (admin user: %s)", settings.auth_username)
    else:
        logger.warning("Authentication DISABLED — API is open. Set AUTH_PASSWORD to require login.")
    yield


app = FastAPI(
    title="AI Meeting Intelligence Platform",
    description="Audio → transcript → diarisation → summary → action items → searchable RAG archive.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list or ["*"],
    allow_credentials=False,  # no cookies are used; lets "*" origins work for the deployed SPA
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# /api/auth/* and /api/health stay public; everything else requires a valid token
# (a no-op when auth is disabled, i.e. AUTH_PASSWORD unset).
app.include_router(auth.router)

_protected = [Depends(require_auth)]
app.include_router(meetings.router, dependencies=_protected)
app.include_router(speakers.router, dependencies=_protected)
app.include_router(action_items.router, dependencies=_protected)
app.include_router(search.router, dependencies=_protected)
app.include_router(analytics.router, dependencies=_protected)
