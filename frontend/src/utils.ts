export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m >= 60) {
    const h = Math.floor(m / 60);
    return `${h}h ${m % 60}m`;
  }
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatTime(seconds: number | null): string {
  if (seconds === null || seconds === undefined || seconds < 0) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  converting: "Converting audio",
  transcribing: "Transcribing",
  diarising: "Identifying speakers",
  analysing: "Analysing with Gemini",
  indexing: "Indexing for search",
  done: "Done",
  error: "Error",
};

export const STAGE_ORDER = [
  "queued",
  "converting",
  "transcribing",
  "diarising",
  "analysing",
  "indexing",
  "done",
];

export function stageProgress(stage: string): number {
  const i = STAGE_ORDER.indexOf(stage);
  if (i < 0) return 0;
  return Math.round((i / (STAGE_ORDER.length - 1)) * 100);
}
