from __future__ import annotations

import asyncio
import pytest
from orchestrator_agent.settings import Settings
from orchestrator_agent.workflow import (
    run_analyze_workflow,
    run_analyze_workflow_stream,
    run_chat_workflow,
    run_chat_workflow_stream,
)
from shared.payloads import AgentSnapshot, SynthesizerOut


@pytest.mark.asyncio
async def test_orchestrator_workflow_uses_orchestrated_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run(*_args, **_kwargs) -> SynthesizerOut:
        return SynthesizerOut(executive_summary="summary", report="# Final")

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_for_idea", fake_run)
    res = await run_analyze_workflow("idea", Settings())
    assert res.report == "# Final"


@pytest.mark.asyncio
async def test_orchestrator_stream_emits_orchestrator_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run(*_args, snapshot_queue: asyncio.Queue[AgentSnapshot], **_kwargs) -> SynthesizerOut:
        snapshot_queue.put_nowait(
            AgentSnapshot(
                agent="research",
                status="started",
                summary="starting",
                full_text="Research started",
            )
        )
        return SynthesizerOut(executive_summary="", report="# Final")

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_for_idea", fake_run)
    events = [ev async for ev in run_analyze_workflow_stream("idea", Settings())]
    assert events[0].step == "orchestrator"
    assert events[0].status == "started"
    assert any(ev.step == "agent_update" and ev.agent_snapshot is not None for ev in events)
    assert events[-1].step == "complete"
    assert events[-1].report == "# Final"


@pytest.mark.asyncio
async def test_chat_workflow_preserves_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat(*_args, **_kwargs) -> str:
        return "assistant reply"

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_chat", fake_chat)
    resp = await run_chat_workflow(
        "hello",
        Settings(),
        session_id="session-1",
        thread_id="thread-1",
    )
    assert resp.session_id == "session-1"
    assert resp.thread_id == "thread-1"
    assert resp.assistant_message == "assistant reply"


@pytest.mark.asyncio
async def test_chat_stream_emits_agent_updates(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat(
        *_args,
        snapshots: list[AgentSnapshot],
        snapshot_queue: asyncio.Queue[AgentSnapshot],
        **_kwargs,
    ) -> str:
        started = AgentSnapshot(
            agent="research",
            status="started",
            summary="starting",
            full_text="Research started",
        )
        completed = AgentSnapshot(
            agent="research",
            status="completed",
            summary="short",
            full_text="long result",
        )
        snapshots.extend([started, completed])
        snapshot_queue.put_nowait(started)
        await asyncio.sleep(0.01)
        snapshot_queue.put_nowait(completed)
        return "assistant reply"

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_chat", fake_chat)
    events = [
        ev
        async for ev in run_chat_workflow_stream(
            "hello",
            Settings(),
            session_id="session-1",
            thread_id="thread-1",
        )
    ]
    assert events[0].event == "orchestrator_started"
    agent_events = [ev for ev in events if ev.event == "agent_update"]
    assert len(agent_events) == 2
    assert agent_events[0].agent_snapshot is not None
    assert agent_events[0].agent_snapshot.status == "started"
    assert agent_events[1].agent_snapshot is not None
    assert agent_events[1].agent_snapshot.status == "completed"
    assert events[-1].event == "assistant_completed"
