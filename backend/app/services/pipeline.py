"""End-to-end ingest pipeline.

convert → transcribe (Whisper) → diarise (pyannote) → merge speakers → persist →
analyse (Gemini agents: summary, action items, topics) → index (RAG).

Runs as a FastAPI background task. Each stage updates ``meeting.stage`` so the UI can
poll progress. Individual analysis/indexing failures are non-fatal: a meeting that has a
transcript is still useful, so we complete it and log warnings rather than erroring out.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from ..agents import action_item_agent, summary_agent, topic_agent
from ..database import SessionLocal
from ..models import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_PROCESSING,
    ActionItem,
    Meeting,
    Speaker,
    Summary,
    Topic,
    TranscriptSegment,
)
from . import audio, diarization, transcription, vectorstore

logger = logging.getLogger(__name__)

_CHUNK_MAX_CHARS = 700


def _format_transcript(segments: list[dict]) -> str:
    return "\n".join(f'{seg.get("speaker", "Speaker 1")}: {seg["text"]}' for seg in segments)


def _build_chunks(segments: list[dict], summary: Optional[dict]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    cid = 0
    buf, b_start, b_end, b_speaker = "", None, None, None
    for seg in segments:
        line = f'{seg.get("speaker", "Speaker 1")}: {seg["text"]}'
        if b_start is None:
            b_start, b_speaker = seg["start"], seg.get("speaker")
        buf = f"{buf}\n{line}" if buf else line
        b_end = seg["end"]
        if len(buf) >= _CHUNK_MAX_CHARS:
            chunks.append(
                {"id": f"t{cid}", "text": buf, "type": "transcript",
                 "speaker": b_speaker, "start": b_start, "end": b_end}
            )
            cid += 1
            buf, b_start = "", None
    if buf:
        chunks.append(
            {"id": f"t{cid}", "text": buf, "type": "transcript",
             "speaker": b_speaker, "start": b_start, "end": b_end}
        )

    if summary:
        for key in ("overview", "key_decisions", "discussion_points", "open_questions", "next_steps"):
            val = summary.get(key)
            text = val if isinstance(val, str) else "; ".join(val or [])
            if text and text.strip():
                label = key.replace("_", " ").title()
                chunks.append({"id": f"s_{key}", "text": f"{label}: {text}", "type": "summary"})
    return chunks


def _set_stage(db, meeting: Meeting, stage: str, status: str = STATUS_PROCESSING) -> None:
    meeting.stage = stage
    meeting.status = status
    db.commit()


def process_meeting(meeting_id: int) -> None:
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if not meeting:
            logger.error("process_meeting: meeting %s not found", meeting_id)
            return

        src = Path(meeting.audio_path)
        wav = src.with_suffix(".16k.wav")

        # 1. normalise audio
        _set_stage(db, meeting, "converting")
        audio.ensure_wav(src, wav)
        meeting.duration = audio.get_duration(wav)
        db.commit()

        # 2. transcribe
        _set_stage(db, meeting, "transcribing")
        tr = transcription.transcribe(wav)
        meeting.language = tr.get("language")
        if tr.get("duration"):
            meeting.duration = tr["duration"]
        db.commit()
        segments = tr["segments"]

        if not segments:
            logger.warning("No speech detected in meeting %s", meeting_id)
            meeting.status = STATUS_DONE
            meeting.stage = "done"
            db.commit()
            return

        # 3. diarise + merge
        _set_stage(db, meeting, "diarising")
        turns = diarization.diarize(wav)
        segments, labels = diarization.assign_speakers(segments, turns)

        label_to_id: dict[str, int] = {}
        for lab in labels:
            sp = Speaker(meeting_id=meeting_id, label=lab)
            db.add(sp)
            db.flush()
            label_to_id[lab] = sp.id
        for seg in segments:
            db.add(
                TranscriptSegment(
                    meeting_id=meeting_id,
                    speaker_id=label_to_id.get(seg["speaker"]),
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"],
                )
            )
        db.commit()

        transcript_text = _format_transcript(segments)

        # 4. analyse (each agent independent + non-fatal)
        _set_stage(db, meeting, "analysing")
        summary: Optional[dict] = None
        try:
            summary = summary_agent.summarize(transcript_text)
            db.add(Summary(meeting_id=meeting_id, **summary))
            db.commit()
        except Exception as exc:
            logger.exception("Summary failed for meeting %s: %s", meeting_id, exc)

        try:
            for item in action_item_agent.extract_action_items(transcript_text):
                db.add(ActionItem(meeting_id=meeting_id, **item))
            db.commit()
        except Exception as exc:
            logger.exception("Action items failed for meeting %s: %s", meeting_id, exc)

        try:
            for topic in topic_agent.extract_topics(transcript_text):
                db.add(Topic(meeting_id=meeting_id, topic=topic))
            db.commit()
        except Exception as exc:
            logger.exception("Topics failed for meeting %s: %s", meeting_id, exc)

        # 5. index for RAG (non-fatal)
        _set_stage(db, meeting, "indexing")
        try:
            n = vectorstore.index_meeting(meeting_id, meeting.title, _build_chunks(segments, summary))
            logger.info("Indexed %s chunks for meeting %s", n, meeting_id)
        except Exception as exc:
            logger.exception("Indexing failed for meeting %s: %s", meeting_id, exc)

        meeting.status = STATUS_DONE
        meeting.stage = "done"
        db.commit()
        logger.info("Meeting %s processed successfully", meeting_id)

    except Exception as exc:  # pipeline-level failure
        logger.exception("Pipeline failed for meeting %s", meeting_id)
        try:
            meeting = db.get(Meeting, meeting_id)
            if meeting:
                meeting.status = STATUS_ERROR
                meeting.stage = "error"
                meeting.error = str(exc)[:1000]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
