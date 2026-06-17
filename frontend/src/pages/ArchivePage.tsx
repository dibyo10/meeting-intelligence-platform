import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { badgeClass } from "../colors";
import type { MeetingListItem, SearchResponse } from "../types";
import { formatDate, formatDuration, formatTime, STAGE_LABELS } from "../utils";

export default function ArchivePage() {
  const nav = useNavigate();
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setMeetings(await api.listMeetings());
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Poll while any meeting is still processing.
  useEffect(() => {
    const processing = meetings.some((m) => m.status !== "done" && m.status !== "error");
    if (!processing) return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [meetings]);

  async function doSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setSearching(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.search(q.trim()));
    } catch (e: any) {
      setError(e.message || "Search failed");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Archive</h1>
        <p>Search across every meeting in natural language, or open a meeting below.</p>
      </div>

      <div className="card answer-card" style={{ marginBottom: 22 }}>
        <form className="search-bar" onSubmit={doSearch}>
          <input
            className="input"
            placeholder="Ask anything — e.g. “What did we decide about pricing?”"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="btn btn-primary" disabled={searching}>
            {searching ? <span className="spinner" /> : "Search"}
          </button>
        </form>

        {error && <div className="muted" style={{ marginTop: 12, color: "var(--red)" }}>{error}</div>}

        {result && (
          <div style={{ marginTop: 18 }}>
            <div className="answer">{result.answer}</div>
            {result.matches.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div className="card-title">Sources</div>
                {result.matches.map((m, i) => (
                  <div
                    key={i}
                    className="match"
                    style={{ cursor: "pointer" }}
                    onClick={() => nav(`/meetings/${m.meeting_id}`)}
                  >
                    <div className="match-head">
                      <span className="match-cite">{i + 1}</span>
                      <span>{m.meeting_title}</span>
                      {m.speaker && <span className="faint">· {m.speaker}</span>}
                      {m.start !== null && <span className="faint">· {formatTime(m.start)}</span>}
                      <span className="badge" style={{ marginLeft: 8 }}>{m.type}</span>
                      <span className="match-score">{(m.score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="muted">{m.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card-title">{meetings.length} meeting{meetings.length === 1 ? "" : "s"}</div>
      {meetings.length === 0 ? (
        <div className="empty">
          <div className="e-icon">🗂</div>
          No meetings yet. Upload one to get started.
        </div>
      ) : (
        <div className="meeting-list">
          {meetings.map((m) => {
            const processing = m.status !== "done" && m.status !== "error";
            return (
              <div key={m.id} className="meeting-row" onClick={() => nav(`/meetings/${m.id}`)}>
                <div>
                  <div className="m-title">{m.title}</div>
                  <div className="m-meta">
                    <span>{formatDate(m.created_at)}</span>
                    {m.duration > 0 && <span>· {formatDuration(m.duration)}</span>}
                    <span>· 👥 {m.num_speakers}</span>
                    <span>· ✅ {m.num_action_items}</span>
                  </div>
                </div>
                <div className="m-right">
                  <span className={"badge " + badgeClass(m.status)}>
                    {processing && <span className="spinner" style={{ width: 11, height: 11 }} />}
                    {m.status === "done" ? "Done" : STAGE_LABELS[m.stage] || m.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
