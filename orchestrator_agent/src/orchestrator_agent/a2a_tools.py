"""Orchestrator tool wrappers for A2A Research and Critic agents."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from functools import lru_cache

import httpx
from shared.a2a_client import HttpA2AClient
from shared.payloads import AgentSnapshot, CriticIn, CriticOut, ResearchIn, ResearchOut

from orchestrator_agent.settings import Settings

_snapshot_collector: ContextVar[list[AgentSnapshot] | None] = ContextVar(
    "orchestrator_snapshot_collector",
    default=None,
)
_snapshot_queue: ContextVar[asyncio.Queue[AgentSnapshot] | None] = ContextVar(
    "orchestrator_snapshot_queue",
    default=None,
)


def _summarize_text(text: str, *, limit: int = 180) -> str:
    flat = " ".join(text.strip().split())
    if len(flat) <= limit:
        return flat
    return f"{flat[: limit - 1].rstrip()}..."


def set_snapshot_collector(snapshots: list[AgentSnapshot] | None):
    return _snapshot_collector.set(snapshots)


def set_snapshot_queue(queue: asyncio.Queue[AgentSnapshot] | None):
    return _snapshot_queue.set(queue)


def reset_snapshot_collector(token) -> None:
    _snapshot_collector.reset(token)


def reset_snapshot_queue(token) -> None:
    _snapshot_queue.reset(token)


def _record_snapshot(agent: str, status: str, full_text: str) -> None:
    snapshot = AgentSnapshot(
        agent=agent,
        status=status,
        summary=_summarize_text(full_text),
        full_text=full_text.strip(),
    )
    collector = _snapshot_collector.get()
    if collector is not None:
        collector.append(snapshot)
    queue = _snapshot_queue.get()
    if queue is not None:
        queue.put_nowait(snapshot)


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_a2a_client() -> HttpA2AClient:
    settings = get_settings()
    timeout = httpx.Timeout(settings.http_timeout_seconds)
    return HttpA2AClient(timeout=timeout)


async def call_research_agent(idea: str) -> str:
    """Call the Research A2A service and return validated JSON text."""
    settings = get_settings()
    client = get_a2a_client()
    _record_snapshot("research", "started", f"Research started for: {idea}")
    try:
        raw = await client.invoke(
            settings.research_a2a_url,
            ResearchIn(idea=idea).model_dump_json(),
        )
        validated = ResearchOut.parse_loose(raw).model_dump_json()
        _record_snapshot("research", "completed", validated)
        return validated
    except Exception as exc:
        _record_snapshot("research", "failed", f"Research failed: {exc}")
        raise


async def call_critic_agent(idea: str, research: str) -> str:
    """Call the Critic A2A service using idea and research JSON text."""
    settings = get_settings()
    client = get_a2a_client()
    research_obj = ResearchOut.parse_loose(research).model_dump()
    _record_snapshot("critic", "started", f"Critic started for: {idea}")
    try:
        raw = await client.invoke(
            settings.critic_a2a_url,
            CriticIn(idea=idea, research=research_obj).model_dump_json(),
        )
        validated = CriticOut.parse_loose(raw).model_dump_json()
        _record_snapshot("critic", "completed", validated)
        return validated
    except Exception as exc:
        _record_snapshot("critic", "failed", f"Critic failed: {exc}")
        raise
