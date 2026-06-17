import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

function fmt(t: number) {
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function UploadPage() {
  const nav = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [recTime, setRecTime] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | undefined>(undefined);

  function pick(f: File | null) {
    if (!f) return;
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ""));
  }

  async function startRec() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        pick(new File([blob], `live-recording.webm`, { type: "audio/webm" }));
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
      setRecTime(0);
      timerRef.current = window.setInterval(() => setRecTime((t) => t + 1), 1000);
    } catch {
      setError("Microphone access denied or unavailable.");
    }
  }

  function stopRec() {
    mediaRef.current?.stop();
    setRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  }

  async function submit() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const m = await api.uploadMeeting(file, title || undefined);
      nav(`/meetings/${m.id}`);
    } catch (e: any) {
      setError(e.message || "Upload failed");
      setUploading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>New meeting</h1>
        <p>Upload a recording or capture live audio. We'll transcribe, identify speakers,
          summarise, extract action items, and index it for search — usually in under two minutes.</p>
      </div>

      <div className="card">
        <div
          className={"dropzone" + (drag ? " drag" : "")}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            pick(e.dataTransfer.files?.[0] ?? null);
          }}
        >
          <div className="dz-icon">{file ? "🎧" : "⬆️"}</div>
          <div className="dz-title">{file ? file.name : "Drop audio/video here or click to browse"}</div>
          <div className="dz-sub">
            {file
              ? `${(file.size / 1024 / 1024).toFixed(1)} MB · ready to upload`
              : "MP3, WAV, M4A, MP4, WEBM…"}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="audio/*,video/*"
            style={{ display: "none" }}
            onChange={(e) => pick(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className="row" style={{ marginTop: 16, justifyContent: "center" }}>
          <span className="faint">or</span>
          {!recording ? (
            <button className="btn btn-sm" onClick={startRec}>🎙️ Record live</button>
          ) : (
            <button className="btn btn-sm btn-danger" onClick={stopRec}>
              ⏹ Stop · {fmt(recTime)}
            </button>
          )}
        </div>

        <div style={{ marginTop: 20 }}>
          <label className="card-title" style={{ display: "block" }}>Meeting title</label>
          <input
            className="input"
            placeholder="e.g. Weekly product sync"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        {error && <div className="toast error" style={{ position: "static", marginTop: 16 }}>{error}</div>}

        <div className="row" style={{ marginTop: 20, justifyContent: "flex-end" }}>
          <button className="btn btn-primary" disabled={!file || uploading} onClick={submit}>
            {uploading ? <><span className="spinner" /> Uploading…</> : "Process meeting →"}
          </button>
        </div>
      </div>
    </div>
  );
}
