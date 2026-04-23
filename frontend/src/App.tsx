import "./App.css";
import { AgentCards } from "./components/AgentCards";
import { ChatComposer } from "./components/ChatComposer";
import { ChatTranscript } from "./components/ChatTranscript";
import { useChatStream } from "./hooks/useChatStream";

function App() {
  const { messages, agentCards, sessionId, threadId, loading, error, sendMessage } =
    useChatStream();

  return (
    <div className="app">
      <div className="app__bg" aria-hidden />
      <main className="app-shell">
        <aside className="app-sidebar">
          <div className="sidebar-brand">
            <p className="sidebar-brand__badge">A2A · Deep Agents</p>
            <h1>AgentMesh</h1>
            <p>Live orchestration console</p>
          </div>
          <AgentCards cards={agentCards} />
        </aside>

        <section className="workspace">
          <header className="workspace-header">
            <div>
              <h2>Orchestrator Chat</h2>
              <p>Send tasks and monitor agent progress in one workspace.</p>
            </div>
            <p className="chat-meta">
              Session: {sessionId ?? "not started"} · Thread: {threadId ?? "not started"}
            </p>
          </header>

          <div className="workspace-body">
            <ChatTranscript messages={messages} />
          </div>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <footer className="workspace-composer">
            <ChatComposer onSend={sendMessage} disabled={loading} />
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
