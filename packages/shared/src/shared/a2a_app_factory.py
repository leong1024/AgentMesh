"""Construct FastAPI apps for A2A JSON-RPC servers."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from fastapi import FastAPI


def build_a2a_fastapi(agent_card: AgentCard, executor: AgentExecutor) -> FastAPI:
    handler = DefaultRequestHandler(executor, InMemoryTaskStore())
    builder = A2AFastAPIApplication(agent_card=agent_card, http_handler=handler)
    return builder.build(title=agent_card.name)
