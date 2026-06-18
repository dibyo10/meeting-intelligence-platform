"""Pydantic schemas for API requests and responses."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until the token expires


class IdentityResponse(BaseModel):
    username: str
    auth_enabled: bool


# ---------- nested ----------
class SpeakerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    display_name: Optional[str] = None


class SegmentOut(BaseModel):
    id: int
    start: float
    end: float
    text: str
    speaker_id: Optional[int] = None
    speaker_label: Optional[str] = None
    speaker_name: Optional[str] = None


class ActionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    completed: bool = False


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    overview: Optional[str] = None
    attendees: list[str] = []
    key_decisions: list[str] = []
    discussion_points: list[str] = []
    open_questions: list[str] = []
    next_steps: list[str] = []


# ---------- meetings ----------
class MeetingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    duration: float
    status: str
    stage: str
    num_speakers: int = 0
    num_action_items: int = 0


class MeetingDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    duration: float
    status: str
    stage: str
    error: Optional[str] = None
    language: Optional[str] = None
    speakers: list[SpeakerOut] = []
    segments: list[SegmentOut] = []
    summary: Optional[SummaryOut] = None
    action_items: list[ActionItemOut] = []
    topics: list[str] = []


# ---------- mutations ----------
class RenameSpeakerRequest(BaseModel):
    display_name: str


class ToggleActionItemRequest(BaseModel):
    completed: bool


class UpdateMeetingRequest(BaseModel):
    title: str


# ---------- search ----------
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    meeting_id: Optional[int] = None


class SearchMatch(BaseModel):
    meeting_id: int
    meeting_title: str
    type: str
    speaker: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    text: str
    score: float


class SearchResponse(BaseModel):
    query: str
    answer: str
    matches: list[SearchMatch] = []


# ---------- analytics ----------
class SpeakingTimeItem(BaseModel):
    speaker: str
    seconds: float
    percentage: float


class FrequencyItem(BaseModel):
    period: str
    count: int


class TopicItem(BaseModel):
    topic: str
    count: int


class AnalyticsOverview(BaseModel):
    total_meetings: int
    total_duration: float
    total_action_items: int
    completed_action_items: int
    completion_rate: float
    speaking_time: list[SpeakingTimeItem] = []
    frequency: list[FrequencyItem] = []
    top_topics: list[TopicItem] = []
