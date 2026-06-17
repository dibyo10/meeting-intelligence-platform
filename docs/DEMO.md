# Demo Script (≈ 4 minutes)

A tight walkthrough that hits every required feature and success metric.

## Before you start
- Backend running (`uvicorn app.main:app --port 8000`) with `GEMINI_API_KEY` + `HF_TOKEN` set.
- Frontend running (`npm run dev`).
- Have `samples/standup.wav` ready (3 distinct voices: Sarah/PM, David/Eng, Raj/Design).

## Talking track

**1. The problem (15s).** "Meetings lose decisions and follow-ups. This turns any recording
into a structured, searchable knowledge asset in under two minutes."

**2. Upload / live (30s).** New Meeting page → drag in `standup.wav` (or hit **Record live**
to capture from the mic). Click **Process meeting**. Show the live status bar moving through
*transcribing → identifying speakers → analysing → indexing*.
→ *Feature: Audio transcription + live capture.*

**3. Transcript + diarisation (45s).** Open the meeting → **Transcript** tab.
- Point out word-accurate transcription of clean audio (**WER < 10%**).
- Show the **3 speakers** detected; click a speaker chip and rename `Speaker 1 → Sarah`.
- Click a timestamp to seek the audio player.
→ *Features: Transcription, Speaker diarisation (≥3 speakers), rename.*

**4. Structured summary (30s).** **Summary** tab — overview, attendees, **key decisions**
(ship pricing page Tuesday), **discussion points**, **open questions** (annual billing),
**next steps**. Note topic chips.
→ *Feature: Structured summary with all sections.*

**5. Action items (30s).** **Action items** tab — checkable list with owner + deadline
(e.g. *David — backend changes — Thursday*; *Raj — mockups — tomorrow*; *David — perf
regression — Friday*). Tick one to show completion tracking.
→ *Feature: Action-item extraction (captures all explicit tasks).*

**6. Searchable archive / RAG (45s).** Archive page → ask in natural language:
- "What did we decide about pricing?"
- "Who owns the performance investigation?"
- "Were there any open questions?"
Show the synthesised answer **with cited sources** that link back to the meeting.
→ *Feature: Searchable archive (≥5 NL queries).*

**7. Analytics (30s).** Analytics page — speaking time per participant, action-item
completion rate, recurring topics, meeting frequency over time.
→ *Feature: Meeting analytics.*

**8. Architecture one-liner (15s).** "Whisper + pyannote for voice, `gemini-3.1-pro-preview`
for all reasoning, Gemini embeddings + ChromaDB for RAG, FastAPI + React. Each meeting is
processed by a staged pipeline of specialised agents."

## Suggested extra queries for the RAG metric (≥5)
1. What did we decide about pricing?
2. When will the backend changes be ready?
3. Who is responsible for the mockups?
4. What open questions came up?
5. What is the plan for the performance regression?
