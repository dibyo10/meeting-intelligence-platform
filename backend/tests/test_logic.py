"""Unit tests for pure pipeline/agent logic (no network, no ML deps)."""
from app import models
from app.agents.gemini_client import _as_str_list, _extract_balanced, _parse_json
from app.database import SessionLocal, init_db
from app.services import analytics
from app.services.diarization import assign_speakers
from app.services.pipeline import _build_chunks


# ---------- robust JSON parsing ----------
def test_parse_json_plain():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_code_fence():
    assert _parse_json('```json\n{"a": [1, 2]}\n```') == {"a": [1, 2]}


def test_parse_json_embedded_in_prose():
    assert _parse_json('Sure! Here you go: {"x": "y"} hope that helps') == {"x": "y"}


def test_extract_balanced_nested():
    assert _extract_balanced('xx {"a": {"b": 1}} yy', "{", "}") == '{"a": {"b": 1}}'


def test_as_str_list_coercions():
    assert _as_str_list(None) == []
    assert _as_str_list("solo") == ["solo"]
    assert _as_str_list(["a", "", "  b  "]) == ["a", "b"]
    assert _as_str_list([{"text": "hi"}, {"name": "yo"}]) == ["hi", "yo"]


# ---------- chunking ----------
def test_build_chunks_splits_and_adds_summary():
    segs = [
        {"start": 0.0, "end": 2.0, "speaker": "Speaker 1", "text": "x" * 400},
        {"start": 2.0, "end": 4.0, "speaker": "Speaker 2", "text": "y" * 400},
        {"start": 4.0, "end": 6.0, "speaker": "Speaker 1", "text": "wrap up"},
    ]
    summary = {"overview": "ov", "key_decisions": ["d1", "d2"], "open_questions": []}
    chunks = _build_chunks(segs, summary)

    assert all(c["text"].strip() for c in chunks)
    transcript_ids = {c["id"] for c in chunks if c["type"] == "transcript"}
    summary_ids = {c["id"] for c in chunks if c["type"] == "summary"}
    assert len(transcript_ids) >= 2                  # long text forced a split
    assert "s_overview" in summary_ids
    assert "s_key_decisions" in summary_ids
    assert "s_open_questions" not in summary_ids     # empty section skipped


# ---------- speaker assignment / merge ----------
def test_assign_speakers_single_when_no_turns():
    segs = [{"start": 0.0, "end": 1.0, "text": "a"}, {"start": 1.0, "end": 2.0, "text": "b"}]
    out, labels = assign_speakers(segs, [])
    assert labels == ["Speaker 1"]
    assert all(s["speaker"] == "Speaker 1" for s in out)


def test_assign_speakers_maps_in_order_of_appearance():
    segs = [{"start": 0.0, "end": 1.0, "text": "a"}, {"start": 1.0, "end": 2.0, "text": "b"}]
    turns = [
        {"start": 0.0, "end": 1.0, "speaker": "SPEAKER_07"},
        {"start": 1.0, "end": 2.0, "speaker": "SPEAKER_03"},
    ]
    out, labels = assign_speakers(segs, turns)
    assert labels == ["Speaker 1", "Speaker 2"]
    assert out[0]["speaker"] == "Speaker 1"
    assert out[1]["speaker"] == "Speaker 2"


# ---------- agent output normalisation (LLM call mocked) ----------
def test_action_item_normalisation(monkeypatch):
    from app.agents import action_item_agent

    monkeypatch.setattr(
        action_item_agent, "generate_json",
        lambda *a, **k: {"action_items": [
            {"task": "Send the report", "owner": "Alice", "deadline": "Friday"},
            {"description": "Review PR", "assignee": "Bob", "due": "null"},
            {"task": "   ", "owner": "x"},     # dropped: empty task
            "Ship the release",                # bare string -> task
        ]},
    )
    out = action_item_agent.extract_action_items("transcript")
    tasks = {x["task"] for x in out}
    assert "Send the report" in tasks
    assert "Ship the release" in tasks
    assert all(x["task"].strip() for x in out)        # blank task removed
    review = next(x for x in out if x["task"] == "Review PR")
    assert review["owner"] == "Bob"
    assert review["deadline"] is None                 # "null" cleaned out


def test_topic_normalisation_dedup_and_cap(monkeypatch):
    from app.agents import topic_agent

    monkeypatch.setattr(
        topic_agent, "generate_json",
        lambda *a, **k: {"topics": ["Hiring", "hiring", "  API  Design "] + [f"t{i}" for i in range(10)]},
    )
    out = topic_agent.extract_topics("x")
    assert out[0] == "hiring"
    assert out.count("hiring") == 1                   # case-insensitive dedup
    assert "api design" in out                        # whitespace normalised
    assert len(out) <= 8


def test_summary_normalisation(monkeypatch):
    from app.agents import summary_agent

    monkeypatch.setattr(
        summary_agent, "generate_json",
        lambda *a, **k: {
            "overview": "  A sync.  ",
            "attendees": "Alice",                     # str -> list
            "key_decisions": ["Ship v1", {"text": "Hire"}],
            "discussion_points": None,
        },
    )
    out = summary_agent.summarize("x")
    assert out["overview"] == "A sync."
    assert out["attendees"] == ["Alice"]
    assert "Ship v1" in out["key_decisions"] and "Hire" in out["key_decisions"]
    assert out["discussion_points"] == []
    assert out["open_questions"] == []                # missing key -> []


# ---------- analytics aggregation ----------
def test_analytics_overview():
    init_db()
    db = SessionLocal()
    try:
        m = models.Meeting(title="M1", duration=120.0, status="done", stage="done")
        db.add(m)
        db.flush()
        sp = models.Speaker(meeting_id=m.id, label="Speaker 1", display_name="Alice")
        db.add(sp)
        db.flush()
        db.add(models.TranscriptSegment(meeting_id=m.id, speaker_id=sp.id, start=0.0, end=30.0, text="hi"))
        db.add(models.ActionItem(meeting_id=m.id, task="t1", completed=True))
        db.add(models.ActionItem(meeting_id=m.id, task="t2", completed=False))
        db.add(models.Topic(meeting_id=m.id, topic="hiring"))
        db.commit()

        ov = analytics.overview(db)
        assert ov["total_meetings"] >= 1
        assert ov["total_action_items"] >= 2
        assert ov["completed_action_items"] >= 1
        assert 0.0 <= ov["completion_rate"] <= 1.0
        assert any(s["speaker"] == "Alice" for s in ov["speaking_time"])
        assert any(t["topic"] == "hiring" for t in ov["top_topics"])
    finally:
        db.close()
