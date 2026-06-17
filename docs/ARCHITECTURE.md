# Architecture

## Overview

```
                          ┌──────────────────────────────────────────────┐
   Upload / Live mic ───▶ │  FastAPI backend                              │
                          │                                               │
                          │  1. Ingest (save file, create Meeting row)    │
                          │  2. Transcribe   → faster-whisper             │
                          │  3. Diarise      → pyannote.audio             │
                          │  4. Merge        → speaker-labelled segments  │
                          │  5. Agents (gemini-3.1-pro-preview):          │
                          │       • SummaryAgent                          │
                          │       • ActionItemAgent                       │
                          │       • TopicAgent                            │
                          │  6. Index        → gemini-embedding-001 +     │
                          │                    ChromaDB                   │
                          └───────────────┬───────────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              ▼                            ▼                           ▼
        SQLite (relational)        ChromaDB (vectors)          Analytics service
   meetings, speakers,            chunk embeddings of         speaking time, frequency,
   segments, action_items,        transcript + summary        completion rate, topics
   summaries, topics
              ▲                            ▲
              └──────── SearchAgent (RAG) ─┘   ◀── natural-language queries
                                          │
                                  React + Vite frontend
                          (Upload · Archive/Search · Detail · Analytics)
```

The whole ingest pipeline runs in a background task so the upload request returns
immediately; the frontend polls meeting status (`queued → transcribing → diarising →
analysing → indexing → done`).

## Components

### Transcription (`services/transcription.py`)
- `faster-whisper` (`WhisperModel`) with `word_timestamps=True`.
- Returns segments `{start, end, text, words[]}`.
- Model size / device / compute type are configurable; `int8` on CPU for speed.

### Diarisation (`services/diarization.py`)
- `pyannote.audio` `Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")`.
- Produces `{start, end, speaker}` turns.
- **Merge:** each Whisper segment is assigned the speaker whose turns overlap it most.
- **Graceful degradation:** if `HF_TOKEN` is missing/invalid, everything is labelled
  `Speaker 1` and the rest of the pipeline still works.

### Agents (`agents/`)
All use `gemini-3.1-pro-preview` through a single defensive client
(`agents/gemini_client.py`) that:
- requests `response_mime_type="application/json"`,
- sets `thinking_config(thinking_level=...)`,
- supports `system_instruction`,
- **degrades gracefully** — if the installed SDK rejects a parameter, it retries without it,
- robustly parses JSON (strips code fences) and validates with Pydantic.

- **SummaryAgent** → `{attendees, key_decisions, discussion_points, open_questions, next_steps}`
- **ActionItemAgent** → `[{task, owner, deadline}]`
- **TopicAgent** → `[topic]` (normalised keywords for recurring-topic analytics)
- **SearchAgent** → retrieves top-k chunks from ChromaDB and synthesises a cited answer

### RAG (`services/embeddings.py`, `services/vectorstore.py`)
- Chunk transcript (by speaker turn / window) + the summary sections.
- Embed with `gemini-embedding-001` (`task_type=RETRIEVAL_DOCUMENT`, 768-dim).
- Store in ChromaDB with metadata `{meeting_id, type, speaker, start, end}`.
- Query embeds with `task_type=RETRIEVAL_QUERY`; results carry citations.

### Analytics (`services/analytics.py`)
- **Speaking time:** sum of segment durations grouped by resolved speaker name.
- **Frequency:** meetings grouped by day/week.
- **Completion rate:** `completed / total` action items.
- **Recurring topics:** topic frequency across meetings.

## Data model (SQLite via SQLAlchemy)
- `meetings(id, title, created_at, duration, audio_path, status, error)`
- `speakers(id, meeting_id, label, display_name)`
- `transcript_segments(id, meeting_id, speaker_id, start, end, text)`
- `action_items(id, meeting_id, task, owner, deadline, completed)`
- `summaries(meeting_id, attendees, key_decisions, discussion_points, open_questions, next_steps)` (JSON columns)
- `topics(id, meeting_id, topic)`

## API surface (FastAPI)
- `POST /api/meetings` — upload audio (multipart), starts pipeline → `{id, status}`
- `GET  /api/meetings` — list
- `GET  /api/meetings/{id}` — detail (transcript, summary, action items, speakers, status)
- `DELETE /api/meetings/{id}` — delete (DB + vectors + file)
- `POST /api/meetings/{id}/reprocess` — re-run pipeline
- `PATCH /api/speakers/{id}` — rename speaker
- `PATCH /api/action-items/{id}` — toggle completion
- `POST /api/search` — `{query}` → cited RAG answer + matches
- `GET  /api/analytics/...` — speaking-time, frequency, completion, topics

## Key decisions
- **Python 3.11 venv** — system Python is 3.14, which lacks torch/pyannote/ctranslate2 wheels.
- **Gemini model in one constant** (`config.GEMINI_MODEL`) — swap models in one place.
- **google-genai over ADK for the agent layer** — chosen for reliability of the unattended
  build; an ADK orchestration layer is planned as an additive bonus and does not block the product.
- **Background pipeline + status polling** — keeps the upload endpoint responsive and the
  UI honest about long-running transcription.
