# Features — Living Log

This document is updated continuously as features are built. It is the single source of
truth for **what exists, its status, and how it maps to the assignment requirements**.

**Status legend:** ✅ done · 🚧 in progress · ⬜ planned

---

## Core features (assignment requirements)

### 1. Audio Transcription — ⬜
- Upload audio/video files; transcribe with `faster-whisper` (word-level timestamps).
- Robust to multiple speakers, background noise, and technical vocabulary.
- Config: model size / device / compute type via `.env`.
- **Success metric:** WER < 10% on clear audio.

### 2. Speaker Diarisation — ⬜
- `pyannote.audio` (`speaker-diarization-3.1`) detects & labels speakers.
- Whisper segments are assigned to speakers by time-overlap.
- Post-processing **rename UI**: map `Speaker 1 → "Alice"`; persists across summary/analytics.
- **Success metric:** correctly separates ≥ 3 speakers.

### 3. Action Item Extraction — ⬜
- `gemini-3.1-pro-preview` extracts commitments: **task, owner, deadline** (when stated).
- Presented as a **checkable list**; completion state persisted; feeds completion-rate analytics.
- **Success metric:** captures all explicitly stated tasks.

### 4. Structured Summary — ⬜
- Sections: **attendees · key decisions · discussion points · open questions · next steps**.
- Generated with a forced JSON schema; faithful to the transcript.
- **Success metric:** all sections present & accurate.

### 5. Searchable Archive (RAG) — ⬜
- Transcript + summary chunked, embedded with `gemini-embedding-001`, stored in ChromaDB.
- Natural-language search across the **whole archive**; answers cite source meetings/segments.
- **Success metric:** relevant results for ≥ 5 test queries.

### 6. Meeting Analytics — ⬜
- Speaking time per participant (from diarisation durations).
- Meeting frequency over time; action-item completion rate; recurring topics across meetings.

---

## Supporting features
- ⬜ Live microphone recording in-browser (the "join live" interpretation).
- ⬜ Background processing with live status (queued → transcribing → diarising → analysing → done).
- ⬜ Meeting archive list with search + filters.
- ⬜ Per-meeting detail view (transcript, summary, action items, speakers).
- ⬜ Optional ADK orchestration layer (bonus).

---

## Changelog
- **2026-06-18** — Repo scaffolded; stack finalised (Whisper + pyannote + FastAPI + React + Gemini 3.1 Pro Preview); docs, .gitignore, requirements, env template initialised; git repo created.
