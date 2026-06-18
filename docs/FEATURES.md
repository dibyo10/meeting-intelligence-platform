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

### 2. Speaker Diarisation — ✅ (verified live)
- `pyannote.audio` 4.x detects & labels speakers from the **audio** (voice embeddings),
  merged onto Whisper segments by time-overlap.
- Friendly labels (`Speaker 1..N`) + **rename UI** to assign real names.
- Graceful single-speaker fallback when no `HF_TOKEN`.
- **Verified:** the 3-voice sample is correctly separated into Speaker 1/2/3, each segment
  attributed to the right voice. ✓ success metric (≥3 speakers).

### 3. Action Item Extraction — ✅ (verified live)
- `gemini-2.5-flash` extracts **task / owner / deadline**; checkable & persisted; feeds
  completion-rate analytics.
- **Verified:** 4/4 explicit tasks captured with correct owners + deadlines on the sample.

### 4. Structured Summary — ✅ (verified live)
- Sections: **attendees · key decisions · discussion points · open questions · next steps**
  via forced JSON schema. **Verified:** all sections populated correctly on the sample; the
  defensive client also auto-recovered from a transient Gemini `503`.

### 5. Searchable Archive (RAG) — ✅ (verified live)
- Transcript + summary chunked, embedded with `gemini-embedding-001` (768-dim), stored in ChromaDB.
- NL search across the whole archive; answers cite source meetings/speakers/timestamps.
- **Verified:** "What did we decide about pricing?" → grounded, citation-tagged answer.

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
  `gemini-2.5-flash` with list/transcript/search tools — construction verified; run via
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
- **2026-06-18** — Repo scaffolded; stack finalised (Whisper + pyannote + FastAPI + React + gemini-2.5-flash).
- **2026-06-18** — Backend core (config, ORM, schemas), Whisper + pyannote services, Gemini agents,
  embeddings + ChromaDB + RAG, ingest pipeline, analytics, FastAPI routers.
- **2026-06-18** — Frontend (upload+mic, archive+search, detail, analytics); builds clean.
- **2026-06-18** — PyAV audio path (system ffmpeg independence), lifespan init, graceful search.
- **2026-06-18** — End-to-end verified offline; deps locked; sample meeting seeded.
- **2026-06-18** — **Live-verified with real keys**: summary, action items, topics, RAG search,
  and analytics all working on `gemini-2.5-flash`. Diarisation switched to a
  torchcodec-free waveform load; multi-speaker output pending HF model-license acceptance.
- **2026-06-18** — **Diarisation fully working**: 3 voices correctly separated into Speaker 1/2/3
  (fixed pyannote 4.x `DiarizeOutput.speaker_diarization` API + HF token env export).
  **🎉 All six core features verified live.**
