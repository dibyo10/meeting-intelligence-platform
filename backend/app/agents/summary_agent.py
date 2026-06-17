"""SummaryAgent — produces a structured meeting summary with all required sections."""
from __future__ import annotations

from .gemini_client import _as_str_list, generate_json

SYSTEM = (
    "You are an expert meeting analyst. You read a speaker-labelled meeting transcript and "
    "produce a faithful, structured summary. Never invent facts that are not supported by the "
    "transcript. Be concise and specific."
)

PROMPT = """\
Analyse the meeting transcript below and return a JSON object with EXACTLY these keys:

{{
  "overview": "2-3 sentence executive summary of the meeting",
  "attendees": ["names or speaker labels of everyone who participated"],
  "key_decisions": ["each concrete decision that was made"],
  "discussion_points": ["the main topics discussed, one per item"],
  "open_questions": ["questions raised but not resolved"],
  "next_steps": ["agreed next steps / follow-ups at a high level"]
}}

Rules:
- Use only information present in the transcript.
- If a section has nothing, return an empty list (or "" for overview).
- For attendees, prefer real names if mentioned, otherwise use the speaker labels.
- Output ONLY the JSON object, no prose, no markdown fences.

TRANSCRIPT:
{transcript}
"""


def summarize(transcript_text: str) -> dict:
    data = generate_json(PROMPT.format(transcript=transcript_text), system_instruction=SYSTEM)
    if not isinstance(data, dict):
        data = {}
    return {
        "overview": str(data.get("overview", "") or "").strip(),
        "attendees": _as_str_list(data.get("attendees")),
        "key_decisions": _as_str_list(data.get("key_decisions")),
        "discussion_points": _as_str_list(data.get("discussion_points")),
        "open_questions": _as_str_list(data.get("open_questions")),
        "next_steps": _as_str_list(data.get("next_steps")),
    }
