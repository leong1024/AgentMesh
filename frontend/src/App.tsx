import "./App.css";
import { IdeaForm } from "./components/IdeaForm";
import { ReportView } from "./components/ReportView";
import { useAnalyzeStream } from "./hooks/useAnalyzeStream";

function App() {
  const { steps, report, loading, error, run } = useAnalyzeStream();

  return (
    <div className="app">
      <header className="header">
        <h1>AgentMesh</h1>
        <p className="tagline">Research → Critic → Synthesizer (Deep Agents + A2A)</p>
      </header>
      <main>
        <IdeaForm onSubmit={run} disabled={loading} />
        {loading && (
          <p className="run-status" role="status">
            Running agents (Research → Critic → Synthesizer)… This can take a minute. Steps
            update as each phase finishes.
          </p>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        {steps.length > 0 && (
          <ol className="steps">
            {steps.map((s, i) => (
              <li key={`${s.step}-${i}`}>
                <strong>{s.step}</strong>: {s.status}
              </li>
            ))}
          </ol>
        )}
        {report && (
          <section className="report-section">
            <h2>Report</h2>
            <ReportView markdown={report} />
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
