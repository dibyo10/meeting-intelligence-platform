import type {
  AnalyticsOverview,
  Health,
  MeetingDetail,
  MeetingListItem,
  SearchResponse,
  Speaker,
  ActionItem,
} from "../types";

const BASE = (import.meta as any).env?.VITE_API_BASE ?? "";

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  return (ct.includes("application/json") ? res.json() : res.text()) as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => req<Health>("/api/health"),

  listMeetings: () => req<MeetingListItem[]>("/api/meetings"),
  getMeeting: (id: number) => req<MeetingDetail>(`/api/meetings/${id}`),
  uploadMeeting: (file: File, title?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (title) fd.append("title", title);
    return req<MeetingListItem>("/api/meetings", { method: "POST", body: fd });
  },
  deleteMeeting: (id: number) => req<unknown>(`/api/meetings/${id}`, { method: "DELETE" }),
  reprocessMeeting: (id: number) =>
    req<MeetingListItem>(`/api/meetings/${id}/reprocess`, { method: "POST" }),
  renameMeeting: (id: number, title: string) =>
    req<MeetingListItem>(`/api/meetings/${id}`, json({ title })),

  renameSpeaker: (id: number, display_name: string) =>
    req<Speaker>(`/api/speakers/${id}`, json({ display_name })),
  toggleActionItem: (id: number, completed: boolean) =>
    req<ActionItem>(`/api/action-items/${id}`, json({ completed })),

  search: (query: string, opts?: { top_k?: number; meeting_id?: number }) =>
    req<SearchResponse>("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, ...opts }),
    }),

  analytics: () => req<AnalyticsOverview>("/api/analytics/overview"),

  audioUrl: (id: number) => `${BASE}/api/meetings/${id}/audio`,
};
