import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AnalyticsOverview } from "../types";
import { formatDuration } from "../utils";

export default function AnalyticsPage() {
  const [a, setA] = useState<AnalyticsOverview | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.analytics().then(setA).catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="page"><div className="empty">⚠️ {err}</div></div>;
  if (!a) return <div className="page"><div className="empty"><span className="spinner" /> Loading…</div></div>;

  const maxFreq = Math.max(1, ...a.frequency.map((f) => f.count));
  const maxTopic = Math.max(1, ...a.top_topics.map((t) => t.count));

  return (
    <div className="page">
      <div className="page-head">
        <h1>Analytics</h1>
        <p>Trends across your entire meeting archive.</p>
      </div>

      {a.total_meetings === 0 ? (
        <div className="empty"><div className="e-icon">📊</div>No data yet — process a few meetings first.</div>
      ) : (
        <>
          <div className="stat-grid">
            <div className="stat"><div className="v accent">{a.total_meetings}</div><div className="l">Meetings</div></div>
            <div className="stat"><div className="v">{formatDuration(a.total_duration)}</div><div className="l">Total duration</div></div>
            <div className="stat"><div className="v">{a.total_action_items}</div><div className="l">Action items</div></div>
            <div className="stat">
              <div className="v">{(a.completion_rate * 100).toFixed(0)}%</div>
              <div className="l">{a.completed_action_items}/{a.total_action_items} completed</div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginTop: 18 }}>
            <div className="card">
              <div className="card-title">Speaking time per participant</div>
              {a.speaking_time.length === 0 ? (
                <div className="muted">No speaker data.</div>
              ) : (
                a.speaking_time.map((s, i) => (
                  <div className="bar-row" key={i}>
                    <div className="bar-label" title={s.speaker}>{s.speaker}</div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${s.percentage}%` }}>
                        {s.percentage >= 12 ? `${s.percentage}%` : ""}
                      </div>
                    </div>
                    <div className="bar-val">{formatDuration(s.seconds)}</div>
                  </div>
                ))
              )}
            </div>

            <div className="card">
              <div className="card-title">Recurring topics</div>
              {a.top_topics.length === 0 ? (
                <div className="muted">No topics yet.</div>
              ) : (
                a.top_topics.map((t, i) => (
                  <div className="bar-row" key={i}>
                    <div className="bar-label" title={t.topic}>{t.topic}</div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${(t.count / maxTopic) * 100}%` }} />
                    </div>
                    <div className="bar-val">{t.count}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="card" style={{ marginTop: 18 }}>
            <div className="card-title">Meeting frequency</div>
            <div className="freq-chart">
              {a.frequency.map((f, i) => (
                <div
                  key={i}
                  className="freq-bar"
                  style={{ height: `${(f.count / maxFreq) * 100}%` }}
                  title={`${f.period}: ${f.count}`}
                >
                  <span>{f.period.slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
