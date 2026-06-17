"""ChromaDB persistent vector store for transcript + summary chunks.

Each meeting's chunks are stored with metadata so search results can cite the source
meeting, speaker, and timestamp. We always supply our own embeddings, so Chroma never
needs its default embedding model.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import get_settings
from . import embeddings as emb

logger = logging.getLogger(__name__)

_COLLECTION = "meeting_chunks"
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb

        s = get_settings()
        _client = chromadb.PersistentClient(path=str(s.chroma_dir))
        _collection = _client.get_or_create_collection(
            _COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def delete_meeting(meeting_id: int) -> None:
    try:
        _get_collection().delete(where={"meeting_id": meeting_id})
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to delete vectors for meeting %s: %s", meeting_id, exc)


def index_meeting(meeting_id: int, title: str, chunks: list[dict[str, Any]]) -> int:
    """Index chunks for one meeting. `chunks`: [{id, text, type, speaker?, start?, end?}].

    Returns the number of chunks indexed. Replaces any existing vectors for the meeting.
    """
    chunks = [c for c in chunks if (c.get("text") or "").strip()]
    if not chunks:
        return 0

    col = _get_collection()
    delete_meeting(meeting_id)

    texts = [c["text"] for c in chunks]
    vectors = emb.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    ids = [f"{meeting_id}:{c['id']}" for c in chunks]
    metadatas = [
        {
            "meeting_id": int(meeting_id),
            "meeting_title": title or "Untitled meeting",
            "type": c.get("type", "transcript"),
            "speaker": c.get("speaker") or "",
            "start": float(c["start"]) if c.get("start") is not None else -1.0,
            "end": float(c["end"]) if c.get("end") is not None else -1.0,
        }
        for c in chunks
    ]
    col.add(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)
    return len(chunks)


def query(text: str, top_k: int, meeting_id: Optional[int] = None) -> list[dict[str, Any]]:
    col = _get_collection()
    qvec = emb.embed_query(text)
    where = {"meeting_id": int(meeting_id)} if meeting_id is not None else None
    res = col.query(query_embeddings=[qvec], n_results=top_k, where=where)

    matches: list[dict[str, Any]] = []
    ids = res.get("ids") or [[]]
    if not ids or not ids[0]:
        return matches
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    for doc, md, dist in zip(docs, metas, dists):
        start = md.get("start")
        end = md.get("end")
        matches.append(
            {
                "meeting_id": int(md.get("meeting_id", 0)),
                "meeting_title": md.get("meeting_title", "Untitled meeting"),
                "type": md.get("type", "transcript"),
                "speaker": (md.get("speaker") or None) or None,
                "start": None if start is None or start < 0 else float(start),
                "end": None if end is None or end < 0 else float(end),
                "text": doc,
                "score": round(1.0 - float(dist), 4),
            }
        )
    return matches
