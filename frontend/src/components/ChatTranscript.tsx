import { ReportView } from "./ReportView";
import type { ChatMessage } from "../types/chat";

type Props = {
  messages: ChatMessage[];
};

export function ChatTranscript({ messages }: Props) {
  return (
    <section className="chat-transcript" aria-label="Conversation transcript">
      {messages.length === 0 ? (
        <p className="chat-transcript__empty">
          Start the conversation. The orchestrator will keep context across turns.
        </p>
      ) : (
        messages.map((msg) => (
          <article
            key={msg.id}
            className={[
              "chat-message",
              msg.role === "user" ? "chat-message--user" : "chat-message--assistant",
            ].join(" ")}
          >
            <header>{msg.role === "user" ? "You" : "Orchestrator"}</header>
            {msg.role === "assistant" ? (
              <ReportView markdown={msg.content} />
            ) : (
              <p>{msg.content}</p>
            )}
          </article>
        ))
      )}
    </section>
  );
}
