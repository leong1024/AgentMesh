import { useState } from "react";

import type { AgentCard } from "../types/chat";

type Props = {
  cards: AgentCard[];
};

export function AgentCards({ cards }: Props) {
  const [selected, setSelected] = useState<AgentCard | null>(null);
  return (
    <>
      <section className="agent-cards" aria-label="Agent updates">
        {cards.map((card) => (
          <button
            type="button"
            key={card.agent}
            className={`agent-card agent-card--${card.status}`}
            onClick={() => setSelected(card)}
          >
            <div className="agent-card__head">
              <h3>{card.agent}</h3>
              <span>{card.status}</span>
            </div>
            <p>{card.summary || "No updates yet."}</p>
          </button>
        ))}
      </section>
      {selected && (
        <dialog className="agent-card-dialog" open onClose={() => setSelected(null)}>
          <div className="agent-card-dialog__header">
            <h3>{selected.agent}</h3>
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
