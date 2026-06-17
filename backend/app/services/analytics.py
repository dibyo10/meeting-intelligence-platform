"""Analytics aggregations across the meeting archive."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ActionItem, Meeting, Speaker, Topic, TranscriptSegment


def overview(db: Session) -> dict:
    meetings = db.execute(select(Meeting)).scalars().all()
    total_meetings = len(meetings)
    total_duration = round(sum(m.duration or 0.0 for m in meetings), 1)

    # action items / completion rate
    items = db.execute(select(ActionItem)).scalars().all()
    total_ai = len(items)
    completed = sum(1 for i in items if i.completed)
    completion_rate = round(completed / total_ai, 4) if total_ai else 0.0

    # speaking time per participant (resolved display name), archive-wide
    speakers = {sp.id: sp for sp in db.execute(select(Speaker)).scalars().all()}
    segments = db.execute(select(TranscriptSegment)).scalars().all()
    times: dict[str, float] = {}
    for seg in segments:
        sp = speakers.get(seg.speaker_id)
        name = sp.name if sp else "Unknown"
        times[name] = times.get(name, 0.0) + max(0.0, (seg.end or 0.0) - (seg.start or 0.0))
    total_speak = sum(times.values()) or 1.0
    speaking_time = [
        {"speaker": name, "seconds": round(sec, 1), "percentage": round(100 * sec / total_speak, 1)}
        for name, sec in sorted(times.items(), key=lambda kv: -kv[1])
    ]

    # meeting frequency by day
    freq: dict[str, int] = {}
    for m in meetings:
        day = m.created_at.strftime("%Y-%m-%d")
        freq[day] = freq.get(day, 0) + 1
    frequency = [{"period": day, "count": freq[day]} for day in sorted(freq)]

    # recurring topics
    topics = db.execute(select(Topic)).scalars().all()
    counts: dict[str, int] = {}
    for t in topics:
        counts[t.topic] = counts.get(t.topic, 0) + 1
    top_topics = [
        {"topic": topic, "count": c}
        for topic, c in sorted(counts.items(), key=lambda kv: -kv[1])
    ][:15]

    return {
        "total_meetings": total_meetings,
        "total_duration": total_duration,
        "total_action_items": total_ai,
        "completed_action_items": completed,
        "completion_rate": completion_rate,
        "speaking_time": speaking_time,
        "frequency": frequency,
        "top_topics": top_topics,
    }
