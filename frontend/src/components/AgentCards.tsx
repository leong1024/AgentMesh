import { useState } from "react";

import type { AgentCard, AgentStatus } from "../types/chat";

type Props = {
  cards: AgentCard[];
};

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  orchestrator: "Orchestrator Agent",
  research: "Research Agent",
  critic: "Critic Agent",
};

function formatAgentName(agentId: string): string {
  return AGENT_DISPLAY_NAMES[agentId] ?? agentId;
}

function statusMeta(status: AgentStatus): {
  label: string;
  icon: string;
  visual: "idle" | "working" | "completed" | "failed";
} {
  if (status === "started" || status === "buffering") {
    return { label: "Buffering", icon: "", visual: "working" };
  }
  if (status === "in_progress") {
    return { label: "Working", icon: "", visual: "working" };
  }
  if (status === "completed") {
    return { label: "Done", icon: "✓", visual: "completed" };
  }
  if (status === "failed") {
    return { label: "Failed", icon: "✕", visual: "failed" };
  }
  return { label: "Idle", icon: "○", visual: "idle" };
}

function statusClass(status: AgentStatus): string {
  if (status === "buffering") return "started";
  if (status === "in_progress") return "started";
  return status;
}

export function AgentCards({ cards }: Props) {
  const [selected, setSelected] = useState<AgentCard | null>(null);
  return (
    <>
      <section className="agent-panel" aria-label="Agent updates">
        <header className="agent-panel__header">
          <h2>🤖🧠</h2>
          <p>Realtime status from orchestrator snapshots.</p>
        </header>
        <div className="agent-cards">
          {cards.map((card) => (
            (() => {
              const meta = statusMeta(card.status);
              return (
                <button
                  type="button"
                  key={card.agent}
                  className={`agent-card agent-card--${statusClass(card.status)}`}
                  onClick={() => setSelected(card)}
                >
                  <div className="agent-card__head">
                    <h3>
                      {formatAgentName(card.agent)}
                      <small>{card.agent}</small>
                    </h3>
                    <span
                      className={`agent-card__status agent-card__status--${meta.visual}`}
                      role="img"
                      aria-label={meta.label}
                      title={meta.label}
                    >
                      {meta.visual === "working" ? (
                        <i className="agent-card__status-spinner" aria-hidden />
                      ) : (
                        meta.icon
                      )}
                    </span>
                  </div>
                  <p>{card.summary || "No updates yet."}</p>
                </button>
              );
            })()
          ))}
        </div>
      </section>
      {selected && (
        <div className="agent-card-modal" role="presentation" onClick={() => setSelected(null)}>
          <div
            className="agent-card-dialog"
            role="dialog"
            aria-modal="true"
            aria-label={`${formatAgentName(selected.agent)} details`}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="agent-card-dialog__header">
              <h3>{formatAgentName(selected.agent)}</h3>
              <button type="button" onClick={() => setSelected(null)}>
                Close
              </button>
            </div>
            <pre>{selected.fullText || "No detailed output yet."}</pre>
          </div>
        </div>
      )}
    </>
  );
}
