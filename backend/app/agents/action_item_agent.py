"""ActionItemAgent — extracts commitments (task, owner, deadline) from the transcript."""
from __future__ import annotations

from typing import Any, Optional

from .gemini_client import generate_json

SYSTEM = (
    "You extract action items from meeting transcripts. An action item is any concrete task, "
    "commitment, or follow-up that someone agreed to do. Capture EVERY explicitly stated task. "
    "Do not invent tasks that were not actually committed to."
)

PROMPT = """\
From the meeting transcript below, extract ALL action items. Return a JSON object:

{{
  "action_items": [
    {{
      "task": "clear description of what needs to be done",
      "owner": "person responsible, or null if not stated",
      "deadline": "due date/timeframe exactly as mentioned, or null if not stated"
    }}
  ]
}}

Rules:
- Include every explicitly stated commitment, even small ones.
- Keep `task` concise but specific (include the object of the action).
- `owner` is the person/role assigned; use null when unclear.
- `deadline` is a date or timeframe (e.g. "Friday", "next sprint", "EOD"); null if none.
- Output ONLY the JSON object, no prose, no markdown fences.

TRANSCRIPT:
{transcript}
"""


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"null", "none", "n/a", "not stated", "unknown", "-"}:
        return None
    return s


def extract_action_items(transcript_text: str) -> list[dict]:
    data = generate_json(PROMPT.format(transcript=transcript_text), system_instruction=SYSTEM)
    items = data.get("action_items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []

    out: list[dict] = []
    for it in items:
        if not isinstance(it, dict):
            if isinstance(it, str) and it.strip():
                out.append({"task": it.strip(), "owner": None, "deadline": None})
            continue
        task = _clean(it.get("task") or it.get("description") or it.get("action"))
        if not task:
            continue
        out.append(
            {
                "task": task,
                "owner": _clean(it.get("owner") or it.get("assignee")),
                "deadline": _clean(it.get("deadline") or it.get("due") or it.get("due_date")),
            }
        )
    return out
