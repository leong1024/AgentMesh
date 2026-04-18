import { describe, expect, it } from "vitest";

import { extractMarkdownReport } from "./extractMarkdownReport";

describe("extractMarkdownReport", () => {
  it("returns plain markdown as-is", () => {
    expect(extractMarkdownReport("# Hello\n\nBody")).toBe("# Hello\n\nBody");
  });

  it("extracts report field from JSON object string", () => {
    const md = "# Title\n\nParagraph";
    const raw = JSON.stringify({
      executive_summary: "short",
      sections: [],
      report: md,
    });
    expect(extractMarkdownReport(raw)).toBe(md);
  });

  it("falls back to executive_summary when report missing", () => {
    const raw = JSON.stringify({ executive_summary: "Only summary" });
    expect(extractMarkdownReport(raw)).toBe("Only summary");
  });

  it("returns empty for null", () => {
    expect(extractMarkdownReport(null)).toBe("");
  });
});
