# ADK bonus layer

An optional [Google Agent Development Kit](https://google.github.io/adk-docs/) agent that
sits on top of the platform. It's **additive** — the FastAPI product works without it.

`root_agent` is a `meeting_assistant` (`gemini-3.1-pro-preview`) with three tools:
- `list_meetings()` — what's in the archive
- `get_meeting_transcript(meeting_id)` — read one meeting
- `search_archive(query)` — RAG search across all meetings

## Run

```bash
cd backend
pip install -r requirements-adk.txt
pip install "opentelemetry-sdk==1.42.1" "opentelemetry-api==1.42.1"   # keep chromadb happy
export GOOGLE_API_KEY=your_gemini_key      # ADK reads this from the environment

adk web        # opens a chat UI; pick "adk_app"
# or headless:
adk run adk_app
# or programmatically:
python scripts/adk_demo.py "Summarise meeting 1 and list its action items"
```

Try: *"What meetings do we have?"*, *"Summarise meeting 1"*, *"What did we decide about pricing?"*

> Note: `google-adk` declares an older `opentelemetry-sdk` pin that conflicts with chromadb.
> Both run fine on `opentelemetry-sdk==1.42.1`; the second pip command above enforces that.
