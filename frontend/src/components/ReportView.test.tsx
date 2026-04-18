import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportView } from "./ReportView";

describe("ReportView", () => {
  it("renders markdown headings", () => {
    render(
      <ReportView
        markdown={`# Hello

Paragraph.`}
      />,
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Hello");
    expect(screen.getByText("Paragraph.")).toBeInTheDocument();
  });
});
