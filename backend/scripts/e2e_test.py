"""In-process end-to-end test via FastAPI TestClient.

Uploads the sample meeting (which runs the full pipeline synchronously as a background
task), then exercises detail / analytics / search endpoints. Works without API keys —
LLM/RAG steps degrade gracefully when no Gemini key is configured.

Usage:  backend/venv/bin/python backend/scripts/e2e_test.py
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

WAV = BACKEND.parent / "samples" / "standup.wav"


def main() -> None:
    with TestClient(app) as c:
        print("HEALTH:", c.get("/api/health").json())

        with open(WAV, "rb") as f:
            r = c.post(
                "/api/meetings",
                files={"file": ("standup.wav", f, "audio/wav")},
                data={"title": "Weekly product sync"},
                timeout=600,
            )
        print("UPLOAD:", r.status_code, r.json())
        mid = r.json()["id"]

        d = c.get(f"/api/meetings/{mid}").json()
        print(
            f"DETAIL: status={d['status']} stage={d['stage']} segments={len(d['segments'])} "
            f"speakers={len(d['speakers'])} actions={len(d['action_items'])} "
            f"topics={d['topics']} summary={'yes' if d['summary'] else 'no'}"
        )
        if d.get("error"):
            print("  pipeline error:", d["error"])
        if d["segments"]:
            print("  first segment:", d["segments"][0]["speaker_name"], "→", d["segments"][0]["text"][:70])

        print("LIST:", [m["title"] + ":" + m["status"] for m in c.get("/api/meetings").json()])
        print("ANALYTICS:", c.get("/api/analytics/overview").json())
        print("SEARCH:", c.post("/api/search", json={"query": "What did we decide about pricing?"}).json()["answer"][:160])


if __name__ == "__main__":
    main()
