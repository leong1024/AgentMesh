export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

export type AgentStatus = "idle" | "started" | "completed" | "failed";

export type AgentCard = {
  agent: string;
  status: AgentStatus;
  summary: string;
  fullText: string;
  updatedAt: string;
};
