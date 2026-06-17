"""SearchAgent — retrieval-augmented answers over the meeting archive.

Retrieves the top-k most relevant chunks from ChromaDB and asks gemini-3.1-pro-preview to
synthesise a grounded answer that cites its sources as [1], [2], ...
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import get_settings
from ..services import vectorstore
from .gemini_client import generate_text

logger = logging.getLogger(__name__)

SYSTEM = (
    "You are a meeting knowledge assistant. You answer questions using ONLY the provided "
    "excerpts from past meetings. Cite the excerpts you use with bracketed numbers like [1]. "
    "If the excerpts do not contain the answer, say so plainly."
)


def _fmt_time(t: Optional[float]) -> str:
    if t is None or t < 0:
        return ""
    m, s = divmod(int(t), 60)
    return f"{m:02d}:{s:02d}"


def _build_context(matches: list[dict]) -> str:
    lines = []
    for i, m in enumerate(matches, 1):
        loc = m.get("meeting_title", "")
        if m.get("speaker"):
            loc += f" · {m['speaker']}"
        ts = _fmt_time(m.get("start"))
        if ts:
            loc += f" @ {ts}"
        lines.append(f"[{i}] ({loc})\n{m['text']}")
    return "\n\n".join(lines)


def search(query: str, top_k: Optional[int] = None, meeting_id: Optional[int] = None) -> dict[str, Any]:
    s = get_settings()
    k = top_k or s.rag_top_k
    matches = vectorstore.query(query, k, meeting_id=meeting_id)

    if not matches:
        return {
            "query": query,
            "answer": "I couldn't find anything relevant in the meeting archive for that query.",
            "matches": [],
        }

    context = _build_context(matches)
    prompt = (
        f"Meeting excerpts:\n\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer the question using only the excerpts above. Cite sources as [n]. "
        "Be concise and specific."
    )
    try:
        answer = generate_text(prompt, system_instruction=SYSTEM)
    except Exception as exc:
        logger.warning("RAG answer synthesis failed: %s", exc)
        answer = "(Could not generate a synthesised answer; showing the most relevant excerpts below.)"

    return {"query": query, "answer": answer, "matches": matches}
