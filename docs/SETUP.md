# Setup & Run Guide

## 0. Prerequisites

| Need | Why | Notes |
|------|-----|-------|
| **Python 3.11** | torch / pyannote / ctranslate2 wheels | This machine's system Python is 3.14 (too new). `python3.11` lives at `~/.local/bin/python3.11`. |
| Node 18+ & npm | frontend | Already present (Node 25). |
| **Gemini API key** | summary, action items, topics, RAG | [aistudio.google.com](https://aistudio.google.com/apikey) |
| **HuggingFace token** | speaker diarisation (pyannote) | [hf.co/settings/tokens](https://hf.co/settings/tokens) + accept terms (step 3) |
| ffmpeg | *optional* | The app converts audio with **PyAV** (bundled), so a working system ffmpeg is **not required**. |

---

## 1. Backend

```bash
cd backend
python3.11 -m venv venv          # MUST be 3.11
source venv/bin/activate
pip install -r requirements.txt        # or: pip install -r requirements-lock.txt (exact pinned)
cp .env.example .env
```

Edit `backend/.env` and fill in:
```ini
GEMINI_API_KEY=AIza...your key...
GOOGLE_API_KEY=AIza...same key...
HF_TOKEN=hf_...your token...
```

Run it:
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Health check: <http://localhost:8000/api/health> — `gemini_configured` and
`diarisation_configured` should read `true` once keys are set.

> **First upload is slow**: the Whisper model (~150 MB for `base`) and pyannote weights
> download on first use, then cache. Subsequent runs are fast.

---

## 2. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api → :8000)
```

---

## 3. Enable speaker diarisation (HF token)

1. Create a token at <https://hf.co/settings/tokens> (read scope is enough).
2. Accept the model terms (one click each) while logged in — **all three** (pyannote 4.x
   pulls the community model internally):
   - <https://hf.co/pyannote/speaker-diarization-3.1>
   - <https://hf.co/pyannote/speaker-diarization-community-1>
   - <https://hf.co/pyannote/segmentation-3.0>
3. Put the token in `backend/.env` as `HF_TOKEN=...` and restart the backend.

Without this, every segment is labelled `Speaker 1` (the app still works end-to-end).

---

## 4. Smoke tests (no server needed)

```bash
cd backend
./venv/bin/python scripts/selftest.py     # transcription + diarisation on the sample
./venv/bin/python scripts/e2e_test.py      # full pipeline + API via in-process TestClient
```

Regenerate the 3-voice sample (macOS `say`, no ffmpeg):
```bash
# see the commands in samples/ — produces samples/standup.wav (3 distinct voices)
```

---

## 5. After adding keys — light up the LLM features

A meeting processed before you added the Gemini key has a transcript but no summary/search.
Re-run analysis from the meeting page (**↻ Reprocess**) or via API:
```bash
curl -X POST http://localhost:8000/api/meetings/1/reprocess
```
This regenerates the summary, action items, topics, and the search index.

---

## Troubleshooting

- **`no such table: meetings`** — tables are created on app startup (lifespan). If you hit
  this in a script, ensure you use `with TestClient(app) as c:` or call `app.database.init_db()`.
- **System `ffmpeg` errors (`libvpx.11.dylib`)** — pre-existing Homebrew version mismatch.
  The app does **not** use system ffmpeg (PyAV handles conversion). To fix ffmpeg itself:
  install Xcode Command Line Tools (`xcode-select --install`) then `brew reinstall ffmpeg`.
- **Slow transcription on CPU** — lower `WHISPER_MODEL` to `tiny`/`base` in `.env`, or set
  `WHISPER_DEVICE=cuda` on an NVIDIA box. On Apple Silicon, `base`/`small` on CPU is fine for the 2-min target.
- **Diarisation download/auth errors** — re-check the HF token and that you accepted the model terms.
