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

    fireEvent.click(screen.getByRole("button", { name: /research/i }));
    expect(screen.getByText("Long and full agent output")).toBeInTheDocument();
  });
});
