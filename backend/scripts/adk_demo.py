"""Run the ADK meeting_assistant agent headlessly.

Usage:  GOOGLE_API_KEY=... backend/venv/bin/python backend/scripts/adk_demo.py "your question"

Requires the ADK extra (see backend/requirements-adk.txt) and a Gemini key.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from adk_app.agent import root_agent  # noqa: E402

APP = "meeting_intelligence"


async def run(query: str) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id="demo")
    message = types.Content(role="user", parts=[types.Part(text=query)])
    async for event in runner.run_async(user_id="demo", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What meetings do we have, and summarise meeting 1."
    asyncio.run(run(q))
