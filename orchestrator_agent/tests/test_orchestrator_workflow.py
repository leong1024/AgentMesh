from __future__ import annotations

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
    async def fake_run(*_args, **_kwargs) -> SynthesizerOut:
        return SynthesizerOut(executive_summary="", report="# Final")

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_for_idea", fake_run)
    events = [ev async for ev in run_analyze_workflow_stream("idea", Settings())]
    assert events[0].step == "orchestrator"
    assert events[0].status == "started"
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
    async def fake_chat(*_args, snapshots: list[AgentSnapshot], **_kwargs) -> str:
        snapshots.append(
            AgentSnapshot(
                agent="research",
                status="completed",
                summary="short",
                full_text="long result",
            )
        )
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
    assert any(ev.event == "agent_update" for ev in events)
    assert events[-1].event == "assistant_completed"
