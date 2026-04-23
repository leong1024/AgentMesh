import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useChatStream } from "./useChatStream";

function streamFromFrames(frames: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    pull(controller) {
      const next = frames.shift();
      if (next === undefined) {
        controller.close();
        return;
      }
      controller.enqueue(encoder.encode(next));
    },
  });
}

describe("useChatStream", () => {
  it("maps SSE chat events into messages and agent cards", async () => {
    const body = streamFromFrames([
      'data: {"event":"orchestrator_started","session_id":"s1","thread_id":"t1","detail":"working"}\n\n',
      'data: {"event":"agent_update","session_id":"s1","thread_id":"t1","agent_snapshot":{"agent":"research","status":"completed","summary":"Short summary","full_text":"Long text"}}\n\n',
      'data: {"event":"assistant_completed","session_id":"s1","thread_id":"t1","message":"Hello from orchestrator"}\n\n',
    ]);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body,
      }),
    );

    const { result } = renderHook(() => useChatStream());
    await act(async () => {
      await result.current.sendMessage("hello");
    });

    expect(result.current.sessionId).toBe("s1");
    expect(result.current.threadId).toBe("t1");
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].content).toContain("Hello from orchestrator");
    const research = result.current.agentCards.find((c) => c.agent === "research");
    expect(research?.summary).toBe("Short summary");
    vi.unstubAllGlobals();
  });
});
