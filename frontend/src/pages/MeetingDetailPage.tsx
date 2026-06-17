import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { badgeClass, speakerColor } from "../colors";
import type { MeetingDetail } from "../types";
import { formatDate, formatDuration, formatTime, STAGE_LABELS, stageProgress } from "../utils";

type Tab = "summary" | "transcript" | "actions";

export default function MeetingDetailPage() {
  const { id } = useParams();
  const mid = Number(id);
  const nav = useNavigate();
  const [m, setM] = useState<MeetingDetail | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [err, setErr] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleVal, setTitleVal] = useState("");
  const [editSpk, setEditSpk] = useState<number | null>(null);
  const [spkVal, setSpkVal] = useState("");
  const audioRef = useRef<HTMLAudioElement>(null);

  async function load() {
    try {
      const d = await api.getMeeting(mid);
      setM(d);
    } catch (e: any) {
      setErr(e.message || "Failed to load meeting");
    }
  }

  useEffect(() => {
    load();
  }, [mid]);

  useEffect(() => {
    if (!m || m.status === "done" || m.status === "error") return;
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [m]);

  if (err) return <div className="page"><div className="empty">⚠️ {err}</div></div>;
  if (!m) return <div className="page"><div className="empty"><span className="spinner" /> Loading…</div></div>;

  const processing = m.status !== "done" && m.status !== "error";

  function seek(t: number) {
    if (audioRef.current) {
      audioRef.current.currentTime = t;
      audioRef.current.play().catch(() => {});
    }
  }

  async function saveTitle() {
    setEditingTitle(false);
    if (titleVal.trim() && titleVal !== m!.title) {
      await api.renameMeeting(mid, titleVal.trim());
      load();
    }
  }

  async function saveSpeaker(spkId: number) {
    setEditSpk(null);
    if (spkVal.trim()) {
      await api.renameSpeaker(spkId, spkVal.trim());
      load();
    }
  }

  async function toggle(itemId: number, completed: boolean) {
    setM({
      ...m!,
      action_items: m!.action_items.map((a) => (a.id === itemId ? { ...a, completed } : a)),
    });
    try {
      await api.toggleActionItem(itemId, completed);
    } catch {
      load();
    }
  }

  const done = m.action_items.filter((a) => a.completed).length;

  return (
    <div className="page">
      <button className="btn btn-ghost btn-sm" onClick={() => nav("/archive")}>← Archive</button>

      <div className="spread" style={{ margin: "14px 0 6px", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          {editingTitle ? (
            <input
              className="input"
              autoFocus
              value={titleVal}
              onChange={(e) => setTitleVal(e.target.value)}
              onBlur={saveTitle}
              onKeyDown={(e) => e.key === "Enter" && saveTitle()}
              style={{ fontSize: 22, fontWeight: 650 }}
            />
          ) : (
            <h1
              onClick={() => { setEditingTitle(true); setTitleVal(m.title); }}
              style={{ fontSize: 26, cursor: "text" }}
              title="Click to rename"
            >
              {m.title}
            </h1>
          )}
          <div className="m-meta" style={{ marginTop: 8 }}>
            <span>{formatDate(m.created_at)}</span>
            {m.duration > 0 && <span>· {formatDuration(m.duration)}</span>}
            {m.language && <span>· {m.language.toUpperCase()}</span>}
            <span className={"badge " + badgeClass(m.status)} style={{ marginLeft: 6 }}>
              {m.status === "done" ? "Done" : STAGE_LABELS[m.stage] || m.status}
            </span>
          </div>
        </div>
        <div className="row">
          <button className="btn btn-sm" onClick={() => api.reprocessMeeting(mid).then(load)}>↻ Reprocess</button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => {
              if (confirm("Delete this meeting?")) api.deleteMeeting(mid).then(() => nav("/archive"));
            }}
          >
            Delete
          </button>
        </div>
      </div>

      {processing && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="row" style={{ marginBottom: 12 }}>
            <span className="spinner" />
            <b>{STAGE_LABELS[m.stage] || "Processing"}…</b>
            <span className="faint" style={{ marginLeft: "auto" }}>{stageProgress(m.stage)}%</span>
          </div>
          <div className="progress"><div style={{ width: `${stageProgress(m.stage)}%` }} /></div>
        </div>
      )}

      {m.status === "error" && (
        <div className="card" style={{ marginTop: 16, borderColor: "var(--red)" }}>
          <b style={{ color: "var(--red)" }}>Processing failed</b>
          <div className="muted" style={{ marginTop: 8 }}>{m.error}</div>
        </div>
      )}

      {!processing && m.status !== "error" && (
        <>
          <div className="tabs" style={{ marginTop: 22 }}>
            <div className={"tab" + (tab === "summary" ? " active" : "")} onClick={() => setTab("summary")}>Summary</div>
            <div className={"tab" + (tab === "transcript" ? " active" : "")} onClick={() => setTab("transcript")}>
              Transcript ({m.segments.length})
            </div>
            <div className={"tab" + (tab === "actions" ? " active" : "")} onClick={() => setTab("actions")}>
              Action items ({done}/{m.action_items.length})
            </div>
          </div>

          {tab === "summary" && <SummaryTab m={m} />}
          {tab === "transcript" && (
            <TranscriptTab
              m={m}
              audioRef={audioRef}
              seek={seek}
              editSpk={editSpk}
              spkVal={spkVal}
              setEditSpk={setEditSpk}
              setSpkVal={setSpkVal}
              saveSpeaker={saveSpeaker}
            />
          )}
          {tab === "actions" && <ActionsTab m={m} toggle={toggle} />}
        </>
      )}
    </div>
  );
}

function Section({ title, items }: { title: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="summary-section">
      <h4>{title}</h4>
      <ul>{items.map((it, i) => <li key={i}>{it}</li>)}</ul>
    </div>
  );
}

function SummaryTab({ m }: { m: MeetingDetail }) {
  const s = m.summary;
  if (!s) return <div className="empty">No summary was generated for this meeting.</div>;
  return (
    <div className="grid grid-2">
      <div>
        <div className="card">
          <div className="card-title">Overview</div>
          <p style={{ margin: 0 }}>{s.overview || "—"}</p>
          {s.attendees.length > 0 && (
            <>
              <div className="card-title" style={{ marginTop: 18 }}>Attendees</div>
              <div className="chips">{s.attendees.map((a, i) => <span className="chip" key={i}>{a}</span>)}</div>
            </>
          )}
          {m.topics.length > 0 && (
            <>
              <div className="card-title" style={{ marginTop: 18 }}>Topics</div>
              <div className="chips">{m.topics.map((t, i) => <span className="chip" key={i}>{t}</span>)}</div>
            </>
          )}
        </div>
      </div>
      <div>
        <div className="card">
          <Section title="Key decisions" items={s.key_decisions} />
          <Section title="Discussion points" items={s.discussion_points} />
          <Section title="Open questions" items={s.open_questions} />
          <Section title="Next steps" items={s.next_steps} />
          {!s.key_decisions.length && !s.discussion_points.length &&
            !s.open_questions.length && !s.next_steps.length && (
              <div className="muted">No structured details extracted.</div>
            )}
        </div>
      </div>
    </div>
  );
}

function TranscriptTab({ m, audioRef, seek, editSpk, spkVal, setEditSpk, setSpkVal, saveSpeaker }: any) {
  return (
    <div className="card">
      <audio ref={audioRef} controls src={api.audioUrl(m.id)} style={{ width: "100%", marginBottom: 16 }} />

      <div className="card-title">Speakers — click a name to rename</div>
      <div className="chips" style={{ marginBottom: 18 }}>
        {m.speakers.map((sp: any) =>
          editSpk === sp.id ? (
            <input
              key={sp.id}
              className="input"
              autoFocus
              style={{ width: 160, padding: "4px 10px" }}
              value={spkVal}
              onChange={(e) => setSpkVal(e.target.value)}
              onBlur={() => saveSpeaker(sp.id)}
              onKeyDown={(e: any) => e.key === "Enter" && saveSpeaker(sp.id)}
            />
          ) : (
            <span
              key={sp.id}
              className="spk-chip"
              style={{ background: speakerColor(sp.label) + "22", color: speakerColor(sp.label), cursor: "pointer" }}
              onClick={() => { setEditSpk(sp.id); setSpkVal(sp.display_name || sp.label); }}
            >
              {sp.display_name || sp.label} ✎
            </span>
          ),
        )}
      </div>

      {m.segments.map((seg: any) => {
        const name = seg.speaker_name || seg.speaker_label || "Speaker";
        const color = speakerColor(seg.speaker_label || name);
        return (
          <div className="segment" key={seg.id}>
            <div className="seg-time" style={{ cursor: "pointer" }} onClick={() => seek(seg.start)}>
              {formatTime(seg.start)}
            </div>
            <div className="seg-body">
              <div className="seg-speaker" style={{ color }}>{name}</div>
              <div className="seg-text">{seg.text}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ActionsTab({ m, toggle }: { m: MeetingDetail; toggle: (id: number, c: boolean) => void }) {
  if (m.action_items.length === 0)
    return <div className="empty">No action items were found in this meeting.</div>;
  return (
    <div className="card">
      {m.action_items.map((a) => (
        <div className="ai-item" key={a.id}>
          <div
            className={"ai-check" + (a.completed ? " checked" : "")}
            onClick={() => toggle(a.id, !a.completed)}
          >
            {a.completed ? "✓" : ""}
          </div>
          <div style={{ flex: 1 }}>
            <div className={"ai-task" + (a.completed ? " done" : "")}>{a.task}</div>
            <div className="ai-meta">
              {a.owner && <span>👤 <b>{a.owner}</b></span>}
              {a.deadline && <span>📅 <b>{a.deadline}</b></span>}
              {!a.owner && !a.deadline && <span className="faint">no owner / deadline specified</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
