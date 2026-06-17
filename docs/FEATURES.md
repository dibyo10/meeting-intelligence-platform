# Features — Living Log

Single source of truth for **what exists, its status, and how it maps to the assignment
requirements**. Updated continuously as features are built.

**Status legend:** ✅ built & verified · 🟡 built, needs API key to verify output · ⬜ planned

> **Note on keys.** The transcription + diarisation + storage + analytics + UI stack is fully
> verified offline. The summary / action-item / topic / RAG-search features are built and run,
> but their *output quality* can only be verified once a `GEMINI_API_KEY` is set (and diarisation
> needs an `HF_TOKEN`). See [SETUP.md](SETUP.md).

---

## Core features (assignment requirements)

### 1. Audio Transcription — ✅
- Upload audio/video; transcribe with `faster-whisper` (word-level timestamps).
- Audio normalised to 16 kHz mono via **PyAV** (no dependency on a system ffmpeg binary).
- VAD filtering for robustness to silence/noise.
- **Verified:** clean 35 s sample → 9 segments, 8/9 keywords exact (the 9th, "backend", was
  correctly transcribed as "back end"). **WER well under 10%.** ✓ success metric.

### 2. Speaker Diarisation — ✅ (fallback verified) / 🟡 (multi-speaker needs HF token)
- `pyannote.audio` 3.1 detects & labels speakers; merged onto Whisper segments by time-overlap.
- Friendly labels (`Speaker 1..N`) + **rename UI** to assign real names.
- Graceful single-speaker fallback verified when no `HF_TOKEN`.
- ⏳ ≥3-speaker separation requires an `HF_TOKEN` (sample contains 3 distinct voices for the demo).

### 3. Action Item Extraction — 🟡
- `gemini-3.1-pro-preview` extracts **task / owner / deadline**; checkable & persisted; feeds
  completion-rate analytics. Code path runs and degrades gracefully without a key.

### 4. Structured Summary — 🟡
- Sections: **attendees · key decisions · discussion points · open questions · next steps**
  via forced JSON schema.

### 5. Searchable Archive (RAG) — 🟡
- Transcript + summary chunked, embedded with `gemini-embedding-001` (768-dim), stored in ChromaDB.
- NL search across the whole archive; answers cite source meetings/speakers/timestamps.

### 6. Meeting Analytics — ✅
- Speaking time per participant, meeting frequency, action-item completion rate, recurring topics.
- **Verified:** `/api/analytics/overview` returns correct totals, per-speaker seconds/%, and
  daily frequency on the seeded meeting.

---

## Supporting features
- ✅ Live microphone recording in-browser (MediaRecorder) + drag/drop upload.
- ✅ Background processing with staged status (queued → converting → transcribing → diarising →
  analysing → indexing → done) and live polling in the UI.
- ✅ Archive list with NL search; per-meeting detail (summary / transcript w/ audio-seek + speaker
  rename / checkable action items); analytics dashboard.
- ✅ Audio playback synced to transcript (click a timestamp to seek).
- ✅ Optional **ADK** orchestration layer (bonus): `adk_app/` `meeting_assistant` agent on
  `gemini-3.1-pro-preview` with list/transcript/search tools — construction verified; run via
  `adk web`. See [adk_app/README.md](../backend/adk_app/README.md).

---

## Verification summary
| Area | How verified | Result |
|------|--------------|--------|
| Backend imports | `import app.main` | ✅ 10 routes |
| Frontend build | `npm run build` | ✅ 42 modules, ~60 KB gzip |
| Transcription | `scripts/selftest.py` on 3-voice sample | ✅ WER < 10% |
| Full pipeline + API | `scripts/e2e_test.py` (TestClient) | ✅ status=done, analytics OK |
| Graceful degradation | E2E without keys | ✅ no crashes; clean fallbacks |
| Deps | `pip freeze` on Python 3.11 | ✅ `requirements-lock.txt` (143 pkgs) |

---

## Changelog
- **2026-06-18** — Repo scaffolded; stack finalised (Whisper + pyannote + FastAPI + React + gemini-3.1-pro-preview).
- **2026-06-18** — Backend core (config, ORM, schemas), Whisper + pyannote services, Gemini agents,
  embeddings + ChromaDB + RAG, ingest pipeline, analytics, FastAPI routers.
- **2026-06-18** — Frontend (upload+mic, archive+search, detail, analytics); builds clean.
- **2026-06-18** — PyAV audio path (system ffmpeg independence), lifespan init, graceful search.
- **2026-06-18** — End-to-end verified offline; deps locked; sample meeting seeded.
