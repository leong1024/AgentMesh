import { useCallback, useState } from "react";

export type StreamStep = {
  step: string;
  status: string;
  detail?: string | null;
  report?: string | null;
};

function parseSseDataBlock(block: string): Record<string, unknown> | null {
  const trimmed = block.trim();
  if (!trimmed) return null;
  const line = trimmed
    .split("\n")
    .find((l) => l.startsWith("data: "));
  if (!line) return null;
  const json = line.slice("data: ".length).trim();
  if (!json) return null;
  try {
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** Parse SSE `data: {...}` frames from a POST response body (AgentMesh `/api/analyze/stream`). */
export async function* readSseJsonLines(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<Record<string, unknown>> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (!done) {
      buffer += decoder.decode(value as Uint8Array, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const block of parts) {
        const ev = parseSseDataBlock(block);
        if (ev) yield ev;
      }
      continue;
    }

    buffer += decoder.decode(new Uint8Array(), { stream: false });
    for (const block of buffer.split("\n\n")) {
      const ev = parseSseDataBlock(block);
      if (ev) yield ev;
    }
    return;
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
        setSteps((s) => [
          ...s,
          {
            step,
            status,
            detail: ev.detail as string | null,
            report: ev.report as string | null,
          },
        ]);
        if (step === "complete") {
          setReport(
            typeof ev.report === "string"
              ? ev.report
              : String(ev.report ?? ""),
          );
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
