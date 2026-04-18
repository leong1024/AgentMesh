import { useCallback, useState } from "react";

export type StreamStep = {
  step: string;
  status: string;
  detail?: string | null;
  report?: string | null;
};

async function* readSseJsonLines(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<Record<string, unknown>> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const block of parts) {
      const line = block
        .split("\n")
        .find((l) => l.startsWith("data: "));
      if (!line) continue;
      const json = line.slice("data: ".length).trim();
      if (json) yield JSON.parse(json) as Record<string, unknown>;
    }
  }
}

export function useAnalyzeStream() {
  const [steps, setSteps] = useState<StreamStep[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (idea: string) => {
    setLoading(true);
    setError(null);
    setReport(null);
    setSteps([]);
    try {
      const res = await fetch("/api/analyze/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      if (!res.body) throw new Error("No response body");
      for await (const ev of readSseJsonLines(res.body)) {
        const step = String(ev.step ?? "");
        const status = String(ev.status ?? "");
        if (step === "error") {
          setError(String(ev.detail ?? "Unknown error"));
          break;
        }
        setSteps((s) => [...s, { step, status, detail: ev.detail as string | null, report: ev.report as string | null }]);
        if (ev.report && step === "complete") {
          setReport(String(ev.report));
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  return { steps, report, loading, error, run };
}
