import type { StreamStep } from "../hooks/useAnalyzeStream";

const AGENTS = ["orchestrator"] as const;

type AgentId = (typeof AGENTS)[number];

const LABELS: Record<AgentId, { title: string; subtitle: string }> = {
  orchestrator: {
    title: "Orchestrator",
    subtitle: "Deep agent · dynamic A2A orchestration",
  },
};

export type NodeState = "pending" | "active" | "done";

function deriveNodeStates(steps: StreamStep[]): Record<AgentId, NodeState> {
  const states: Record<AgentId, NodeState> = {
    orchestrator: "pending",
  };
  for (const s of steps) {
    if (!AGENTS.includes(s.step as AgentId)) continue;
    const id = s.step as AgentId;
    if (s.status === "started") states[id] = "active";
    if (s.status === "completed") states[id] = "done";
  }
  return states;
}

type Props = {
  steps: StreamStep[];
  loading: boolean;
};

export function AgentPipeline({ steps, loading }: Props) {
  const nodeStates = deriveNodeStates(steps);

  return (
    <div className="agent-pipeline" aria-label="Agent workflow status">
      <div className="agent-pipeline__row">
        {AGENTS.map((id, i) => {
          const state = nodeStates[id];
          const { title, subtitle } = LABELS[id];
          const next = AGENTS[i + 1];
          const edgeActive =
            loading &&
            (state === "active" ||
              (state === "done" && next && nodeStates[next] === "active"));
          return (
            <div key={id} className="agent-pipeline__segment">
              <div
                className={[
                  "agent-node",
                  state === "active" && "agent-node--active",
                  state === "done" && "agent-node--done",
                  state === "pending" && loading && "agent-node--pending",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <span className="agent-node__glyph" aria-hidden>
                  {state === "done" ? "✓" : state === "active" ? "◉" : "○"}
                </span>
                <div className="agent-node__text">
                  <span className="agent-node__title">{title}</span>
                  <span className="agent-node__sub">{subtitle}</span>
                </div>
                <span className="agent-node__state">{state}</span>
              </div>
              {next && (
                <div
                  className={[
                    "agent-edge",
                    edgeActive && "agent-edge--pulse",
                    nodeStates[id] === "done" && "agent-edge--filled",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-hidden
                />
              )}
            </div>
          );
        })}
      </div>
      <p className="agent-pipeline__hint">
        {loading
          ? "Orchestrator is planning and calling Research/Critic over A2A as needed."
          : steps.length > 0
            ? "Run finished. Scroll for the synthesized markdown report."
            : "Submit an idea to activate the mesh."}
      </p>
    </div>
  );
}
