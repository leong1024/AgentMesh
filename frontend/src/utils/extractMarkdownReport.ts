/**
 * When the backend falls back to raw JSON (e.g. loose orchestrator output), the stream
 * `report` may be a full JSON object string. Prefer the nested `report` markdown field.
 */
export function extractMarkdownReport(raw: string | null | undefined): string {
  if (raw == null || raw === "") return "";
  const t = raw.trim();
  if (!t) return "";
  if (t.startsWith("{") || t.startsWith("[")) {
    try {
      const v = JSON.parse(t) as unknown;
      if (v && typeof v === "object" && !Array.isArray(v)) {
        const o = v as Record<string, unknown>;
        if (typeof o.report === "string" && o.report.trim()) {
          return o.report.trim();
        }
        if (typeof o.executive_summary === "string" && o.executive_summary.trim()) {
          return o.executive_summary.trim();
        }
      }
    } catch {
      /* not JSON — use as markdown text */
    }
  }
  return t;
}
