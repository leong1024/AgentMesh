"""Public analyze workflow implemented by the Orchestrator agent."""

from __future__ import annotations

from collections.abc import AsyncIterator
import uuid

from shared.payloads import (
    AgentSnapshot,
    AnalyzeResponse,
    ChatMessageResponse,
    ChatStreamEvent,
    CriticOut,
    ResearchOut,
    StepOutputs,
    StreamEvent,
)

from orchestrator_agent.deep_agent import run_orchestrator_chat, run_orchestrator_for_idea
from orchestrator_agent.settings import Settings


def _final_report(markdown: str, executive_summary: str) -> str:
    if markdown.strip():
        return markdown.strip()
    if executive_summary.strip():
        return executive_summary.strip()
    return ""


async def run_analyze_workflow(idea: str, settings: Settings) -> AnalyzeResponse:
    snapshots: list[AgentSnapshot] = []
    synthesis = await run_orchestrator_for_idea(
        idea,
        settings=settings,
        session_id="analyze-session",
        thread_id=f"analyze-{uuid.uuid4()}",
        snapshots=snapshots,
    )
    return AnalyzeResponse(
        report=_final_report(synthesis.report, synthesis.executive_summary),
        steps=StepOutputs(research=ResearchOut(), critic=CriticOut()),
    )


async def run_analyze_workflow_stream(
    idea: str,
    settings: Settings,
) -> AsyncIterator[StreamEvent]:
    yield StreamEvent(step="orchestrator", status="started", detail="Planning dynamic workflow")
    snapshots: list[AgentSnapshot] = []
    synthesis = await run_orchestrator_for_idea(
        idea,
        settings=settings,
        session_id="analyze-session",
        thread_id=f"analyze-{uuid.uuid4()}",
        snapshots=snapshots,
    )
    report = _final_report(synthesis.report, synthesis.executive_summary)
    yield StreamEvent(step="orchestrator", status="completed", detail="Final report generated")
    yield StreamEvent(step="complete", status="done", report=report)


async def run_chat_workflow(
    message: str,
    settings: Settings,
    *,
    session_id: str | None = None,
    thread_id: str | None = None,
) -> ChatMessageResponse:
    use_session = session_id or str(uuid.uuid4())
    use_thread = thread_id or use_session
    snapshots: list[AgentSnapshot] = []
    assistant_message = await run_orchestrator_chat(
        message,
        settings=settings,
        session_id=use_session,
        thread_id=use_thread,
        snapshots=snapshots,
    )
    return ChatMessageResponse(
        session_id=use_session,
        thread_id=use_thread,
        assistant_message=assistant_message.strip(),
        agent_snapshots=snapshots,
    )


async def run_chat_workflow_stream(
    message: str,
    settings: Settings,
    *,
    session_id: str | None = None,
    thread_id: str | None = None,
) -> AsyncIterator[ChatStreamEvent]:
    use_session = session_id or str(uuid.uuid4())
    use_thread = thread_id or use_session
    yield ChatStreamEvent(
        event="orchestrator_started",
        session_id=use_session,
        thread_id=use_thread,
        detail="Orchestrator is processing your message.",
    )
    snapshots: list[AgentSnapshot] = []
    assistant_message = await run_orchestrator_chat(
        message,
        settings=settings,
        session_id=use_session,
        thread_id=use_thread,
        snapshots=snapshots,
    )
    for snapshot in snapshots:
        yield ChatStreamEvent(
            event="agent_update",
            session_id=use_session,
            thread_id=use_thread,
            agent_snapshot=snapshot,
        )
    yield ChatStreamEvent(
        event="assistant_completed",
        session_id=use_session,
        thread_id=use_thread,
        message=assistant_message.strip(),
    )
