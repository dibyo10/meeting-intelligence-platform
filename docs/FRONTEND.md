# Frontend Guide

The web client for the AI Meeting Intelligence Platform. A single-page app built with
**React 18 + Vite + TypeScript**, talking to the FastAPI backend over a small typed API client.

> Architecture overview: [ARCHITECTURE.md](ARCHITECTURE.md) · Local setup: [SETUP.md](SETUP.md).

---

## Running locally

The dev server proxies `/api` to a backend, so you can run the UI on its own — by default it
targets the deployed Render backend, no local backend required.

```bash
cd frontend
npm install      # first run only
npm run dev      # http://localhost:5173
```

**Develop against a local backend instead:** create `frontend/.env` with
`VITE_API_BASE=http://localhost:8000` (see [`.env.example`](../frontend/.env.example)), then
restart the dev server.

| Script            | What it does                                  |
|-------------------|-----------------------------------------------|
| `npm run dev`     | Vite dev server with HMR on port 5173         |
| `npm run build`   | Type-check + production build to `dist/`      |
| `npm run preview` | Serve the built `dist/` on port 5173          |

---

## Source layout

```
frontend/src/
├── main.tsx                 App bootstrap (React root + Router)
├── App.tsx                  Route table
├── components/
│   └── Layout.tsx           Sidebar nav + backend health panel; wraps every page
├── pages/
│   ├── UploadPage.tsx       "New Meeting" — upload/record + processing status
│   ├── ArchivePage.tsx      Meeting list + natural-language search
│   ├── MeetingDetailPage.tsx  Transcript, summary, action items, speaker rename
│   └── AnalyticsPage.tsx    Cross-meeting analytics
├── api/
│   └── client.ts            Typed fetch wrapper + endpoint map (`api.*`)
├── types.ts                 Shared API response types
├── utils.ts                 Formatting helpers
├── colors.ts                Speaker-colour palette + status badge classes
└── index.css                Global design system (semantic class names)
```

> How data flows through these pages — types, polling, stage machine:
> [FRONTEND_INTERNALS.md](FRONTEND_INTERNALS.md).

---

## Routing

Defined in [`App.tsx`](../frontend/src/App.tsx) with `react-router-dom`:

| Path              | Page                  |
|-------------------|-----------------------|
| `/`               | `UploadPage`          |
| `/archive`        | `ArchivePage`         |
| `/meetings/:id`   | `MeetingDetailPage`   |
| `/analytics`      | `AnalyticsPage`       |
| `*`               | redirect → `/`        |

Every route renders inside `Layout`, which provides the sidebar (nav links + a live backend
health panel showing model, Gemini-key status, diarisation, and Whisper model).

---

## API client

All network calls go through [`api/client.ts`](../frontend/src/api/client.ts). It wraps `fetch`,
prefixes requests with `VITE_API_BASE` (empty in dev so the Vite proxy handles `/api`), parses
JSON, and surfaces backend error `detail` strings as thrown `Error`s.

| Method                              | Endpoint                                  |
|-------------------------------------|-------------------------------------------|
| `api.health()`                      | `GET /api/health`                         |
| `api.listMeetings()`                | `GET /api/meetings`                       |
| `api.getMeeting(id)`                | `GET /api/meetings/:id`                   |
| `api.uploadMeeting(file, title?)`   | `POST /api/meetings` (multipart)          |
| `api.deleteMeeting(id)`             | `DELETE /api/meetings/:id`                |
| `api.reprocessMeeting(id)`          | `POST /api/meetings/:id/reprocess`        |
| `api.renameMeeting(id, title)`      | `PATCH /api/meetings/:id`                 |
| `api.renameSpeaker(id, name)`       | `PATCH /api/speakers/:id`                 |
| `api.toggleActionItem(id, done)`    | `PATCH /api/action-items/:id`             |
| `api.search(query, opts?)`          | `POST /api/search`                        |
| `api.analytics()`                   | `GET /api/analytics/overview`             |
| `api.audioUrl(id)`                  | URL for `GET /api/meetings/:id/audio`     |

When adding a feature that needs a new endpoint, add the method here and the response type in
[`types.ts`](../frontend/src/types.ts) — keep components free of raw `fetch` calls.

---

## Conventions

- **TypeScript everywhere** — response shapes live in `types.ts`, not inline `any`.
- **No raw fetch in components** — go through the `api` object.
- **Styling is global CSS** with semantic class names (`index.css`); there is no CSS-in-JS or
  utility framework.
- **Speaker colours** are derived deterministically from a speaker key via `speakerColor()` in
  `colors.ts`, so the same speaker keeps the same colour across views.
