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
      <header className="header">
        <p className="header__badge">A2A · Deep Agents</p>
        <h1>AgentMesh</h1>
        <p className="tagline">
          Chat with the orchestrator while monitoring Research and Critic outputs live.
        </p>
      </header>
      <main className="main">
        <AgentCards cards={agentCards} />
        <ChatTranscript messages={messages} />
        <ChatComposer onSend={sendMessage} disabled={loading} />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <p className="chat-meta">
          Session: {sessionId ?? "not started"} · Thread: {threadId ?? "not started"}
        </p>
      </main>
    </div>
  );
}

export default App;
