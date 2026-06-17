const PALETTE = [
  "#7c6cff",
  "#4cc9f0",
  "#3ddc97",
  "#ffb454",
  "#ff6b6b",
  "#b072ff",
  "#5ad1c9",
  "#f6a6ff",
];

export function speakerColor(key: string | number): string {
  const s = String(key ?? "");
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

export function badgeClass(status: string): string {
  if (status === "done") return "done";
  if (status === "error") return "error";
  if (status === "queued") return "queued";
  return "processing";
}
