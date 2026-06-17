"""Speaker rename endpoint (assign real names to diarisation labels)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Speaker

router = APIRouter(prefix="/api/speakers", tags=["speakers"])


@router.patch("/{speaker_id}", response_model=schemas.SpeakerOut)
def rename_speaker(
    speaker_id: int, body: schemas.RenameSpeakerRequest, db: Session = Depends(get_db)
):
    sp = db.get(Speaker, speaker_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Speaker not found")
    sp.display_name = body.display_name.strip() or None
    db.commit()
    return schemas.SpeakerOut.model_validate(sp)
