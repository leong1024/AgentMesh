import { useCallback, useMemo, useState } from "react";

import type { AgentCard, ChatMessage } from "../types/chat";

type ChatEvent = {
  event?: string;
  session_id?: string;
  thread_id?: string;
  message?: string;
  detail?: string;
  agent_snapshot?: {
    agent?: string;
    status?: "idle" | "started" | "buffering" | "in_progress" | "completed" | "failed";
    summary?: string;
    full_text?: string;
    updated_at?: string;
  };
};

const SSE_EVENT_BOUNDARY = /\r\n\r\n|\n\n/;

function chatStreamUrl(): string {
  const base = import.meta.env.VITE_ORCHESTRATOR_URL?.replace(/\/$/, "") ?? "";
  return base ? `${base}/api/chat/stream` : "/api/chat/stream";
}

function nextId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function* readSseJsonLines(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<Record<string, unknown>> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (!done) {
      buffer += decoder.decode(value as Uint8Array, { stream: true });
      const parts = buffer.split(SSE_EVENT_BOUNDARY);
      buffer = parts.pop() ?? "";
      for (const block of parts) {
        const line = block
          .trim()
          .split(/\r\n|\n|\r/)
          .find((entry) => entry.startsWith("data: "));
        if (!line) continue;
        try {
          yield JSON.parse(line.slice("data: ".length).trim()) as Record<string, unknown>;
        } catch {
          // Ignore malformed frame and keep stream alive.
        }
      }
      continue;
    }
    return;
  }
}

const DEFAULT_AGENT_CARDS: AgentCard[] = [
  {
    agent: "orchestrator",
    status: "idle",
    summary: "Primary user-facing coordinator.",
    fullText: "The orchestrator plans responses and calls other agents as needed.",
    updatedAt: "",
  },
  {
    agent: "research",
    status: "idle",
    summary: "Awaits orchestrator tool call.",
    fullText: "",
    updatedAt: "",
  },
  {
    agent: "critic",
    status: "idle",
    summary: "Awaits orchestrator tool call.",
    fullText: "",
    updatedAt: "",
  },
];

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [agentCards, setAgentCards] = useState<AgentCard[]>(DEFAULT_AGENT_CARDS);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      const trimmed = message.trim();
      if (!trimmed) return;
      setLoading(true);
      setError(null);
      setMessages((prev) => [...prev, { id: nextId("user"), role: "user", content: trimmed }]);
      try {
        const res = await fetch(chatStreamUrl(), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmed,
            session_id: sessionId ?? undefined,
            thread_id: threadId ?? undefined,
          }),
        });
        if (!res.ok) throw new Error(await res.text());
        if (!res.body) throw new Error("No response body");
        for await (const raw of readSseJsonLines(res.body)) {
          const ev = raw as ChatEvent;
          if (ev.session_id) setSessionId(ev.session_id);
          if (ev.thread_id) setThreadId(ev.thread_id);
          if (ev.event === "error") {
            setError(ev.detail ?? "Unknown error");
            break;
          }
          if (ev.event === "orchestrator_started") {
            setAgentCards((cards) =>
              cards.map((card) =>
                card.agent === "orchestrator"
                  ? {
                      ...card,
                      status: "started",
                      summary: ev.detail ?? card.summary,
                      fullText: ev.detail ?? card.fullText,
                      updatedAt: new Date().toISOString(),
                    }
                  : card,
              ),
            );
          }
          if (ev.event === "agent_update" && ev.agent_snapshot) {
            const snapshot = ev.agent_snapshot;
            const agent = String(snapshot.agent ?? "orchestrator");
            setAgentCards((cards) =>
              cards.map((card) =>
                card.agent === agent
                  ? {
                      ...card,
                      status: snapshot.status ?? "completed",
                      summary: snapshot.summary ?? card.summary,
                      fullText: snapshot.full_text ?? card.fullText,
                      updatedAt: snapshot.updated_at ?? new Date().toISOString(),
                    }
                  : card,
              ),
            );
          }
          if (ev.event === "assistant_completed") {
            const assistantText = String(ev.message ?? "").trim();
            setAgentCards((cards) =>
              cards.map((card) =>
                card.agent === "orchestrator"
                  ? { ...card, status: "completed", updatedAt: new Date().toISOString() }
                  : card,
              ),
            );
            if (assistantText) {
              setMessages((prev) => [
                ...prev,
                { id: nextId("assistant"), role: "assistant", content: assistantText },
              ]);
            }
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [sessionId, threadId],
  );

  return useMemo(
    () => ({
      messages,
      agentCards,
      sessionId,
      threadId,
      loading,
      error,
      sendMessage,
    }),
    [messages, agentCards, sessionId, threadId, loading, error, sendMessage],
  );
}
