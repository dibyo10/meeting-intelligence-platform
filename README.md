# 🎙️ AI Meeting Intelligence Platform

> From meeting chaos to structured decisions — every call becomes a searchable knowledge asset.

Upload a meeting recording (or record live) and get, in under two minutes, a **speaker-labelled transcript**, a **structured summary**, a **checkable action-item list**, and a **searchable archive** you can query in natural language — plus **analytics** across all your meetings.

This is a GenAI course project in the **Voice + RAG** category.

---

## ✨ Features

| # | Feature | How |
|---|---------|-----|
| 1 | **Audio transcription** | `faster-whisper` with word-level timestamps; handles noise & technical vocab |
| 2 | **Speaker diarisation** | `pyannote.audio` labels speakers; rename `Speaker 1 → Alice` post-hoc |
| 3 | **Action-item extraction** | `gemini-3.1-pro-preview` pulls task + owner + deadline into a checkable list |
| 4 | **Structured summary** | Attendees · key decisions · discussion points · open questions · next steps |
| 5 | **Searchable archive (RAG)** | `gemini-embedding-001` + ChromaDB; natural-language search with citations |
| 6 | **Meeting analytics** | Speaking time, meeting frequency, action-item completion rate, recurring topics |

See [`docs/FEATURES.md`](docs/FEATURES.md) for the living feature log and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design.

---

## 🧱 Tech stack

- **Transcription:** faster-whisper (Whisper) · **Diarisation:** pyannote.audio
- **LLM:** `gemini-3.1-pro-preview` (summary, action items, topics, RAG answers) via `google-genai`
- **Embeddings + RAG:** `gemini-embedding-001` + ChromaDB
- **Backend:** FastAPI (Python 3.11) · **Frontend:** React + Vite + TypeScript
- **Storage:** SQLite (metadata, action items) + ChromaDB (vectors)

---

## 🚀 Quick start

> Full details + troubleshooting: [`docs/SETUP.md`](docs/SETUP.md). Demo script: [`docs/DEMO.md`](docs/DEMO.md).

### Prerequisites
- Python **3.11** (the ML stack has no wheels for 3.14 yet; `python3.11` is at `~/.local/bin/python3.11`)
- Node 18+ and npm
- ffmpeg — **optional** (audio is converted with PyAV, which bundles its own ffmpeg libs)
- A **Gemini API key** (Google AI Studio) — for summary / action items / topics / RAG
- A **HuggingFace token** with `pyannote/speaker-diarization-3.1` terms accepted — for multi-speaker diarisation

### 1. Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your keys
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Open the frontend, upload a meeting recording, and watch it get transcribed, summarised, and indexed.

### Verify without the UI
```bash
cd backend
./venv/bin/python scripts/selftest.py   # transcription + diarisation on the sample
./venv/bin/python scripts/e2e_test.py    # full pipeline + API (in-process)
```
> A meeting processed before you added the Gemini key is transcript-only — hit **↻ Reprocess**
> (or `POST /api/meetings/{id}/reprocess`) after adding keys to generate the summary + search index.

---

## 🎯 Success metrics (acceptance targets)

- Transcription WER **< 10%** on clear audio
- Diarisation separates **≥ 3 speakers** on a test recording
- Action-item extraction captures **all explicitly stated** tasks
- Semantic search returns relevant results for **≥ 5 test queries**
- Summary is **structured with all required sections** and faithful to the source

How each is met is tracked in [`docs/FEATURES.md`](docs/FEATURES.md).

---

## 📁 Repo layout
```
meeting-intelligence/
├── backend/          FastAPI app, Whisper/pyannote services, Gemini agents, RAG
├── frontend/         React + Vite UI (upload, archive/search, detail, analytics)
├── docs/             FEATURES.md (living log) + ARCHITECTURE.md
├── data/             SQLite DB, ChromaDB, uploads (gitignored)
└── samples/          sample meeting audio for the demo (gitignored)
```
