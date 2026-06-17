"""SQLAlchemy ORM models for meetings, speakers, transcripts, action items, summaries, topics."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Pipeline status / stage values (kept as plain strings for SQLite simplicity)
STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_ERROR = "error"


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled meeting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    audio_path: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), default=STATUS_QUEUED)
    stage: Mapped[str] = mapped_column(String(32), default=STATUS_QUEUED)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    speakers: Mapped[list["Speaker"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.start"
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    summary: Mapped[Optional["Summary"]] = relationship(
        back_populates="meeting", uselist=False, cascade="all, delete-orphan"
    )
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class Speaker(Base):
    __tablename__ = "speakers"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(64))  # raw diarisation label, e.g. SPEAKER_00
    display_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    meeting: Mapped["Meeting"] = relationship(back_populates="speakers")
    segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="speaker")

    @property
    def name(self) -> str:
        return self.display_name or self.label


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    speaker_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True
    )
    start: Mapped[float] = mapped_column(Float, default=0.0)
    end: Mapped[float] = mapped_column(Float, default=0.0)
    text: Mapped[str] = mapped_column(Text, default="")

    meeting: Mapped["Meeting"] = relationship(back_populates="segments")
    speaker: Mapped[Optional["Speaker"]] = relationship(back_populates="segments")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    task: Mapped[str] = mapped_column(Text)
    owner: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    meeting: Mapped["Meeting"] = relationship(back_populates="action_items")


class Summary(Base):
    __tablename__ = "summaries"

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendees: Mapped[list] = mapped_column(JSON, default=list)
    key_decisions: Mapped[list] = mapped_column(JSON, default=list)
    discussion_points: Mapped[list] = mapped_column(JSON, default=list)
    open_questions: Mapped[list] = mapped_column(JSON, default=list)
    next_steps: Mapped[list] = mapped_column(JSON, default=list)

    meeting: Mapped["Meeting"] = relationship(back_populates="summary")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(128))

    meeting: Mapped["Meeting"] = relationship(back_populates="topics")
