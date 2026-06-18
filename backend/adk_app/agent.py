"""Google ADK (Agent Development Kit) bonus layer.

Exposes a `root_agent` — a `meeting_assistant` LlmAgent powered by `gemini-2.5-flash`
— that can reason over the platform's own data through three tools (list meetings, fetch a
transcript, semantic-search the archive). Run it interactively with:

    cd backend && adk web           # then pick "adk_app" in the web UI
    # or
    cd backend && adk run adk_app

This is an OPTIONAL, additive layer: the FastAPI product does not depend on it. It reuses
the same agents/services, demonstrating an ADK-native multi-tool agent over the archive.

Requires `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) in the environment.
See adk_app/README.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the FastAPI app package importable when ADK loads this module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google.adk.agents import LlmAgent  # noqa: E402

from app.config import get_settings  # noqa: E402

_settings = get_settings()


# ----------------- tools -----------------
def list_meetings() -> list:
    """List every meeting in the archive with its id, title, and processing status."""
    from app.database import SessionLocal
    from app.models import Meeting

    db = SessionLocal()
    try:
        return [{"id": m.id, "title": m.title, "status": m.status} for m in db.query(Meeting).all()]
    finally:
        db.close()


def get_meeting_transcript(meeting_id: int) -> dict:
    """Return the full speaker-labelled transcript and title for a given meeting id.

    Args:
        meeting_id: The numeric id of the meeting (use list_meetings to discover ids).
    """
    from app.database import SessionLocal
    from app.models import Meeting

    db = SessionLocal()
    try:
        m = db.get(Meeting, meeting_id)
        if not m:
            return {"error": f"No meeting with id {meeting_id}"}
        lines = [
            f"{(seg.speaker.name if seg.speaker else 'Speaker')}: {seg.text}" for seg in m.segments
        ]
        return {
            "meeting_id": meeting_id,
            "title": m.title,
            "status": m.status,
            "transcript": "\n".join(lines) or "(no transcript)",
        }
    finally:
        db.close()


def search_archive(query: str) -> dict:
    """Semantic-search the entire meeting archive and return a cited answer with sources.

    Args:
        query: A natural-language question about anything discussed across meetings.
    """
    from app.agents import search_agent

    result = search_agent.search(query)
    return {
        "answer": result["answer"],
        "sources": [
            {"meeting": m["meeting_title"], "speaker": m.get("speaker"), "text": m["text"]}
            for m in result["matches"]
        ],
    }


root_agent = LlmAgent(
    name="meeting_assistant",
    model=_settings.gemini_model,
    description="Assistant that answers questions about recorded meetings and their decisions.",
    instruction=(
        "You are a meeting intelligence assistant. Use the available tools to help the user:\n"
        "- `list_meetings` to see what meetings exist,\n"
        "- `get_meeting_transcript` to read a specific meeting,\n"
        "- `search_archive` for natural-language questions across all meetings.\n"
        "When asked to summarise or extract action items for a meeting, fetch its transcript "
        "first. Always ground answers in tool results and cite the meeting titles you used."
    ),
    tools=[list_meetings, get_meeting_transcript, search_archive],
)
