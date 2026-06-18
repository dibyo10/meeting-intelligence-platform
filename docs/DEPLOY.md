# Deploying on Render

> ⚠️ **Reality check:** this backend bundles `torch` + `pyannote.audio` + `faster-whisper` +
> `chromadb` (~2 GB installed) and downloads model weights at runtime. The **free/starter
> 512 MB instance will OOM**. Use an instance with **≥ 2 GB RAM** (Render "Standard"). For a
> class demo, running locally is cheaper and faster; deploy only if you specifically need a URL.

## Backend (Web Service)

Create a **Web Service** from the repo with:

| Field | Value |
|-------|-------|
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` |
| Instance Type | Standard (≥ 2 GB RAM) |

### Required environment variables
| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.9` — **critical**; 3.12+/3.13 have no torch/pyannote wheels |
| `GEMINI_API_KEY` | your key |
| `GOOGLE_API_KEY` | same key |
| `HF_TOKEN` | your HF token (with the 3 pyannote licences accepted) |
| `DATA_DIR` | `/var/data` (with a persistent disk mounted there) |
| `HF_HOME` | `/var/data/hf-cache` (persist model weights across deploys) |
| `CORS_ORIGINS` | your frontend URL, e.g. `https://meeting-intelligence-web.onrender.com` |

Add a **Disk** (5 GB) mounted at `/var/data` so SQLite, Chroma, and uploads survive restarts.

> Or just commit `render.yaml` (at the repo root) and use Render's **Blueprint** flow — it sets
> all of the above automatically (you still paste the secret keys in the dashboard).

### Why the first deploy failed
Render auto-generated `uvicorn main:app`. The app module is `backend/app/main.py`, so with
Root Directory = `backend` the correct path is **`app.main:app`**. Wrong path → *"Could not
import module 'main'"* → app never binds → *"No open ports detected."* Fixing the Start
Command resolves it.

## Frontend (Static Site)

Separate Render **Static Site**:

| Field | Value |
|-------|-------|
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |
| Env var | `VITE_API_BASE = https://<your-api>.onrender.com` |
| Rewrite rule | `/*` → `/index.html` (SPA routing) |

Then set the backend's `CORS_ORIGINS` to the static-site URL.

## Notes
- ffmpeg is **not** required on the server — audio is converted via PyAV (bundled).
- First request that triggers transcription downloads the Whisper + pyannote weights
  (~300 MB) into `HF_HOME`; with a persistent disk this happens once.
- Cold starts on free tiers also spin the service down; processing a meeting can exceed
  request limits on tiny instances. Another reason to use ≥ 2 GB RAM.
