import { describe, expect, it } from "vitest";

import { readSseJsonLines } from "./useAnalyzeStream";

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    pull(controller) {
      const next = chunks.shift();
      if (next === undefined) {
        controller.close();
        return;
      }
      controller.enqueue(enc.encode(next));
    },
  });
}

describe("readSseJsonLines", () => {
  it("parses multiple well-formed SSE frames", async () => {
    const body = streamFromChunks([
      'data: {"step":"research","status":"started"}\n\n',
      'data: {"step":"research","status":"completed"}\n\n',
    ]);
    const out: Record<string, unknown>[] = [];
    for await (const ev of readSseJsonLines(body)) {
      out.push(ev);
    }
    expect(out).toHaveLength(2);
    expect(out[0]).toMatchObject({ step: "research", status: "started" });
    expect(out[1]).toMatchObject({ step: "research", status: "completed" });
  });

  it("emits final complete event when stream ends without trailing \\n\\n", async () => {
    const payload = JSON.stringify({
      step: "complete",
      status: "done",
      report: "# Hello",
    });
    const body = streamFromChunks([`data: ${payload}`]);
    const out: Record<string, unknown>[] = [];
    for await (const ev of readSseJsonLines(body)) {
      out.push(ev);
    }
    expect(out).toHaveLength(1);
    expect(out[0]).toMatchObject({
      step: "complete",
      status: "done",
      report: "# Hello",
    });
  });

  it("emits complete with empty report string", async () => {
    const payload = JSON.stringify({
      step: "complete",
      status: "done",
      report: "",
    });
    const body = streamFromChunks([`data: ${payload}\n\n`]);
    const out: Record<string, unknown>[] = [];
    for await (const ev of readSseJsonLines(body)) {
      out.push(ev);
    }
    expect(out).toHaveLength(1);
    expect(out[0]).toEqual({
      step: "complete",
      status: "done",
      report: "",
    });
  });

  it("handles event split across chunk boundaries before \\n\\n", async () => {
    const payload = JSON.stringify({ step: "a", status: "b" });
    const frame = `data: ${payload}\n\n`;
    const mid = Math.floor(frame.length / 2);
    const body = streamFromChunks([frame.slice(0, mid), frame.slice(mid)]);
    const out: Record<string, unknown>[] = [];
    for await (const ev of readSseJsonLines(body)) {
      out.push(ev);
    }
    expect(out).toHaveLength(1);
    expect(out[0]).toEqual({ step: "a", status: "b" });
  });
});
