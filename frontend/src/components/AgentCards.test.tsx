import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentCards } from "./AgentCards";

describe("AgentCards", () => {
  it("opens full agent response on card click", () => {
    render(
      <AgentCards
        cards={[
          {
            agent: "research",
            status: "completed",
            summary: "Short summary",
            fullText: "Long and full agent output",
            updatedAt: "2026-01-01T00:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Research Agent")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /research agent/i }));
    expect(screen.getByText("Long and full agent output")).toBeInTheDocument();
  });

  it("falls back to the raw id for unknown agents", () => {
    render(
      <AgentCards
        cards={[
          {
            agent: "qa_bot",
            status: "started",
            summary: "Investigating edge cases",
            fullText: "Checking for regressions",
            updatedAt: "2026-01-01T00:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByRole("button", { name: /qa_bot/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /qa_bot/i }));
    expect(screen.getByRole("heading", { name: "qa_bot" })).toBeInTheDocument();
  });

  it("shows icon-only loading state with accessible label", () => {
    render(
      <AgentCards
        cards={[
          {
            agent: "research",
            status: "started",
            summary: "Working on citations",
            fullText: "Research started",
            updatedAt: "2026-01-01T00:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByLabelText("Buffering")).toBeInTheDocument();
  });
});
