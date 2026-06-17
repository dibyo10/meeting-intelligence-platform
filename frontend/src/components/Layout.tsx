import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { api } from "../api/client";
import type { Health } from "../types";

const links = [
  { to: "/", label: "New Meeting", icon: "＋", end: true },
  { to: "/archive", label: "Archive", icon: "🗂", end: false },
  { to: "/analytics", label: "Analytics", icon: "📊", end: false },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">🎙️</span>
          <div>
            <div className="brand-title">Meeting Intelligence</div>
            <div className="brand-sub">Voice → decisions</div>
          </div>
        </div>

        <nav className="nav">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
            >
              <span className="ico">{l.icon}</span>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {health ? (
            <>
              <div className="row" style={{ gap: 7, marginBottom: 6 }}>
                <span className={"dot " + (health.status === "ok" ? "ok" : "off")} />
                Backend online
              </div>
              <div className="row" title="LLM model">
                <span className="faint">Model</span>
                <span style={{ marginLeft: "auto" }}>{health.model}</span>
              </div>
              <div className="row">
                <span className="faint">Gemini key</span>
                <span className="dot" style={{ marginLeft: "auto" }}
                  data-on={health.gemini_configured} />
              </div>
              <div className="row">
                <span className="faint">Diarisation</span>
                <span style={{ marginLeft: "auto" }}>
                  {health.diarisation_configured ? "on" : "off"}
                </span>
              </div>
              <div className="row">
                <span className="faint">Whisper</span>
                <span style={{ marginLeft: "auto" }}>{health.whisper_model}</span>
              </div>
            </>
          ) : (
            <span className="faint">Connecting to backend…</span>
          )}
        </div>
      </aside>

      <main className="main">{children}</main>
    </div>
  );
}
