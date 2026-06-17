"""TopicAgent — extracts normalised topic tags used for the recurring-topics analytic."""
from __future__ import annotations

from .gemini_client import _as_str_list, generate_json

SYSTEM = (
    "You label meetings with their main topics. Topics are short, reusable tags (1-3 words) "
    "that would group similar meetings together over time, like 'hiring', 'roadmap', "
    "'budget', 'API design'."
)

PROMPT = """\
Read the meeting transcript and return the main topics as a JSON object:

{{
  "topics": ["short topic tag", "another topic tag"]
}}

Rules:
- 3 to 8 topics.
- Each topic is 1-3 words, lowercase, reusable across meetings (not a full sentence).
- Prefer general, recurring themes over one-off specifics.
- Output ONLY the JSON object.

TRANSCRIPT:
{transcript}
"""


def _normalise(topic: str) -> str:
    return " ".join(topic.lower().strip().split())[:64]


def extract_topics(transcript_text: str) -> list[str]:
    data = generate_json(PROMPT.format(transcript=transcript_text), system_instruction=SYSTEM)
    raw = data.get("topics") if isinstance(data, dict) else data
    seen: set[str] = set()
    topics: list[str] = []
    for t in _as_str_list(raw):
        norm = _normalise(t)
        if norm and norm not in seen:
            seen.add(norm)
            topics.append(norm)
    return topics[:8]
