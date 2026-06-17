"""Natural-language RAG search across the meeting archive."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import schemas
from ..agents import search_agent

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=schemas.SearchResponse)
def search(body: schemas.SearchRequest):
    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    return search_agent.search(body.query.strip(), top_k=body.top_k, meeting_id=body.meeting_id)
