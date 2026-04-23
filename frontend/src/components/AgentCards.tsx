import { useState } from "react";

import type { AgentCard } from "../types/chat";

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

export function AgentCards({ cards }: Props) {
  const [selected, setSelected] = useState<AgentCard | null>(null);
  return (
    <>
      <section className="agent-panel" aria-label="Agent updates">
        <header className="agent-panel__header">
          <h2>Agent Cards</h2>
          <p>Realtime status from orchestrator snapshots.</p>
        </header>
        <div className="agent-cards">
          {cards.map((card) => (
            <button
              type="button"
              key={card.agent}
              className={`agent-card agent-card--${card.status}`}
              onClick={() => setSelected(card)}
            >
              <div className="agent-card__head">
                <h3>
                  {formatAgentName(card.agent)}
                  <small>{card.agent}</small>
                </h3>
                <span>{card.status}</span>
              </div>
              <p>{card.summary || "No updates yet."}</p>
            </button>
          ))}
        </div>
      </section>
      {selected && (
        <dialog className="agent-card-dialog" open onClose={() => setSelected(null)}>
          <div className="agent-card-dialog__header">
            <h3>{formatAgentName(selected.agent)}</h3>
            <button type="button" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          <pre>{selected.fullText || "No detailed output yet."}</pre>
        </dialog>
      )}
    </>
  );
}
