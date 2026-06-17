"""Meeting endpoints: upload, list, detail, audio stream, delete, reprocess, rename."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..database import get_db
from ..models import Meeting
from ..services import pipeline, vectorstore

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def _list_item(m: Meeting) -> schemas.MeetingListItem:
    return schemas.MeetingListItem(
        id=m.id,
        title=m.title,
        created_at=m.created_at,
        duration=m.duration,
        status=m.status,
        stage=m.stage,
        num_speakers=len(m.speakers),
        num_action_items=len(m.action_items),
    )


@router.post("", response_model=schemas.MeetingListItem)
def upload_meeting(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    s = get_settings()
    name = (title or "").strip() or Path(file.filename or "meeting").stem or "Untitled meeting"
    meeting = Meeting(title=name, status="queued", stage="queued")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    ext = Path(file.filename or "").suffix or ".audio"
    dest = s.uploads_dir / f"meeting_{meeting.id}{ext}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    meeting.audio_path = str(dest)
    db.commit()

    background.add_task(pipeline.process_meeting, meeting.id)
    return _list_item(meeting)


@router.get("", response_model=list[schemas.MeetingListItem])
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.execute(select(Meeting).order_by(Meeting.created_at.desc())).scalars().all()
    return [_list_item(m) for m in meetings]


@router.get("/{meeting_id}", response_model=schemas.MeetingDetail)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    speakers = {sp.id: sp for sp in m.speakers}
    segments = [
        schemas.SegmentOut(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            text=seg.text,
            speaker_id=seg.speaker_id,
            speaker_label=speakers[seg.speaker_id].label if seg.speaker_id in speakers else None,
            speaker_name=speakers[seg.speaker_id].name if seg.speaker_id in speakers else None,
        )
        for seg in m.segments
    ]
    summary = schemas.SummaryOut.model_validate(m.summary) if m.summary else None

    return schemas.MeetingDetail(
        id=m.id,
        title=m.title,
        created_at=m.created_at,
        duration=m.duration,
        status=m.status,
        stage=m.stage,
        error=m.error,
        language=m.language,
        speakers=[schemas.SpeakerOut.model_validate(sp) for sp in m.speakers],
        segments=segments,
        summary=summary,
        action_items=[schemas.ActionItemOut.model_validate(a) for a in m.action_items],
        topics=[t.topic for t in m.topics],
    )


@router.get("/{meeting_id}/audio")
def get_audio(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m or not m.audio_path or not Path(m.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(m.audio_path)


@router.patch("/{meeting_id}", response_model=schemas.MeetingListItem)
def update_meeting(
    meeting_id: int, body: schemas.UpdateMeetingRequest, db: Session = Depends(get_db)
):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    m.title = body.title.strip() or m.title
    db.commit()
    return _list_item(m)


@router.post("/{meeting_id}/reprocess", response_model=schemas.MeetingListItem)
def reprocess_meeting(
    meeting_id: int, background: BackgroundTasks, db: Session = Depends(get_db)
):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    m.segments.clear()
    m.speakers.clear()
    m.action_items.clear()
    m.topics.clear()
    if m.summary:
        db.delete(m.summary)
    m.status = "queued"
    m.stage = "queued"
    m.error = None
    db.commit()

    vectorstore.delete_meeting(meeting_id)
    background.add_task(pipeline.process_meeting, meeting_id)
    return _list_item(m)


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    for p in (m.audio_path, str(Path(m.audio_path).with_suffix(".16k.wav")) if m.audio_path else None):
        if p:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
    vectorstore.delete_meeting(meeting_id)
    db.delete(m)
    db.commit()
    return {"deleted": meeting_id}
