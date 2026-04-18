import "./App.css";
import { AgentPipeline } from "./components/AgentPipeline";
import { IdeaForm } from "./components/IdeaForm";
import { ReportView } from "./components/ReportView";
import { useAnalyzeStream } from "./hooks/useAnalyzeStream";
import { extractMarkdownReport } from "./utils/extractMarkdownReport";

function App() {
  const { steps, report, loading, error, run } = useAnalyzeStream();
  const showMesh = loading || steps.length > 0;
  const reportMarkdown = report ? extractMarkdownReport(report) : "";

  return (
    <div className="app">
      <div className="app__bg" aria-hidden />
      <header className="header">
        <p className="header__badge">A2A · Deep Agents</p>
        <h1>AgentMesh</h1>
        <p className="tagline">
          Live multi-agent analysis — research, critique, and synthesis in one mesh.
        </p>
      </header>
      <main className="main">
        <IdeaForm onSubmit={run} disabled={loading} />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {showMesh && (
          <section className="mesh-section">
            <AgentPipeline steps={steps} loading={loading} />
            {loading && (
              <p className="run-status" role="status">
                Orchestrator is streaming milestones from each agent. Large ideas can take
                one to two minutes.
              </p>
            )}
            {steps.length > 0 && (
              <details className="event-log">
                <summary>Raw event stream</summary>
                <ol className="steps">
                  {steps.map((s, i) => (
                    <li key={`${s.step}-${i}`}>
                      <strong>{s.step}</strong>: {s.status}
                    </li>
                  ))}
                </ol>
              </details>
            )}
          </section>
        )}
        {reportMarkdown ? (
          <section className="report-section">
            <h2 className="report-section__title">Synthesized report</h2>
            <p className="report-section__sub">Rendered from markdown (GFM).</p>
            <ReportView markdown={report ?? ""} />
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default App;
