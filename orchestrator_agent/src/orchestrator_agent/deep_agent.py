"""Deep Agents graph for the Orchestrator role."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from shared.graph_output import last_ai_text
from shared.model_factory import DEFAULT_GEMINI_MODEL_SPEC, gemini_chat_model
from shared.payloads import AgentSnapshot, CriticOut, ResearchOut, SynthesizerIn, SynthesizerOut
from shared.prompts import ORCHESTRATOR_AGENT_SYSTEM

from orchestrator_agent.a2a_tools import (
    call_critic_agent,
    call_research_agent,
    reset_snapshot_collector,
    set_snapshot_collector,
)
from orchestrator_agent.settings import Settings


def _model(settings: Settings):
    spec = (
        (settings.orchestrator_agent_model or "").strip()
        or DEFAULT_GEMINI_MODEL_SPEC
    )
    return gemini_chat_model(spec)


@lru_cache(maxsize=1)
def get_checkpointer() -> MemorySaver:
    return MemorySaver()


def build_orchestrator_graph(settings: Settings):
    root_dir = str(Path(__file__).parent)
    return create_deep_agent(
        model=_model(settings),
        system_prompt=ORCHESTRATOR_AGENT_SYSTEM,
        tools=(call_research_agent, call_critic_agent),
        backend=FilesystemBackend(root_dir=root_dir),
        skills=["/skills/"],
        checkpointer=get_checkpointer(),
    )


def _compose_prompt(payload: dict[str, Any]) -> str:
    return (
        "Perform dynamic orchestration and synthesis for this product idea.\n"
        "If research/critique are missing or weak, call tools to improve evidence.\n"
        "Return exactly one JSON object only.\n\n"
        f"Input JSON:\n{SynthesizerIn.model_validate(payload).model_dump_json(indent=2)}"
    )


async def run_orchestrator(
    user_payload_json: str,
    *,
    thread_id: str | None = None,
    session_id: str | None = None,
    snapshots: list[AgentSnapshot] | None = None,
    settings: Settings | None = None,
) -> str:
    payload = SynthesizerIn.model_validate_json(user_payload_json)
    use_settings = settings or Settings()
    agent = build_orchestrator_graph(use_settings)
    prompt = _compose_prompt(payload.model_dump())
    config = {
        "configurable": {
            "thread_id": thread_id or "default-thread",
            "session_id": session_id or "default-session",
        }
    }
    token = set_snapshot_collector(snapshots)
    try:
        out = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]}, config=config)
        return last_ai_text(out)
    finally:
        reset_snapshot_collector(token)


async def run_orchestrator_chat(
    message: str,
    *,
    thread_id: str,
    session_id: str,
    snapshots: list[AgentSnapshot] | None = None,
    settings: Settings | None = None,
) -> str:
    use_settings = settings or Settings()
    agent = build_orchestrator_graph(use_settings)
    prompt = (
        "Continue this conversation with the user.\n"
        "You may call research/critic tools whenever they improve the answer.\n"
        "Respond in markdown for a chat UI.\n\n"
        f"User message:\n{message.strip()}"
    )
    config = {"configurable": {"thread_id": thread_id, "session_id": session_id}}
    token = set_snapshot_collector(snapshots)
    try:
        out = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]}, config=config)
        return last_ai_text(out)
    finally:
        reset_snapshot_collector(token)


async def run_orchestrator_for_idea(
    idea: str,
    research: ResearchOut | None = None,
    critic: CriticOut | None = None,
    thread_id: str | None = None,
    session_id: str | None = None,
    snapshots: list[AgentSnapshot] | None = None,
    settings: Settings | None = None,
) -> SynthesizerOut:
    payload = SynthesizerIn(
        idea=idea,
        research=(research or ResearchOut()).model_dump(),
        critique=(critic or CriticOut()).model_dump(),
    )
    raw = await run_orchestrator(
        payload.model_dump_json(),
        thread_id=thread_id,
        session_id=session_id,
        snapshots=snapshots,
        settings=settings,
    )
    return SynthesizerOut.parse_loose(raw)
