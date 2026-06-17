"""Text embeddings via gemini-embedding-001.

Embeddings are L2-normalised (recommended when using a truncated output dimensionality
such as 768/1536), so cosine similarity in ChromaDB behaves well.
"""
from __future__ import annotations

import logging
import math

from ..config import get_settings

logger = logging.getLogger(__name__)

_BATCH = 64  # gemini-embedding-001 batch ceiling is comfortably above this


def _normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _extract_vectors(resp) -> list[list[float]]:
    embeddings = getattr(resp, "embeddings", None)
    if embeddings is None:
        single = getattr(resp, "embedding", None)
        embeddings = [single] if single is not None else []
    out = []
    for e in embeddings:
        values = getattr(e, "values", e)
        out.append([float(x) for x in values])
    return out


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a list of texts. `task_type` is RETRIEVAL_DOCUMENT for indexing,
    RETRIEVAL_QUERY for searches."""
    if not texts:
        return []

    from google.genai import types

    from ..agents.gemini_client import get_client

    s = get_settings()
    client = get_client()
    config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=s.embed_dim)

    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH):
        batch = texts[i : i + _BATCH]
        try:
            resp = client.models.embed_content(
                model=s.gemini_embed_model, contents=batch, config=config
            )
            batch_vecs = _extract_vectors(resp)
        except Exception as exc:
            logger.warning("Batch embed failed (%s); falling back to per-item", exc)
            batch_vecs = []
            for t in batch:
                resp = client.models.embed_content(
                    model=s.gemini_embed_model, contents=t, config=config
                )
                batch_vecs.extend(_extract_vectors(resp))
        vectors.extend(_normalise(v) for v in batch_vecs)

    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]
