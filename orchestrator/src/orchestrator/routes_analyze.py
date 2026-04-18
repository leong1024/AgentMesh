"""Analyze and health routes."""

from __future__ import annotations

import json
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from shared.payloads import AnalyzeRequest, AnalyzeResponse, HealthAgentsResponse
from sse_starlette.sse import EventSourceResponse

from orchestrator.a2a_client import HttpA2AClient
from orchestrator.dependencies import get_a2a_client, get_http_client, get_settings
from orchestrator.settings import Settings
from orchestrator.workflow import run_star_workflow, run_star_workflow_stream

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/api/health/agents", response_model=HealthAgentsResponse)
async def health_agents(
    settings: Annotated[Settings, Depends(get_settings)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> HealthAgentsResponse:
    async def probe(url: str) -> bool:
        try:
            r = await http_client.get(
                f"{url.rstrip('/')}/.well-known/agent-card.json",
            )
            return r.status_code == 200
        except Exception:
            return False

    return HealthAgentsResponse(
        research=await probe(settings.research_a2a_url),
        critic=await probe(settings.critic_a2a_url),
        synthesizer=await probe(settings.synthesizer_a2a_url),
    )


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    body: AnalyzeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[HttpA2AClient, Depends(get_a2a_client)],
) -> AnalyzeResponse:
    logger.info("POST /api/analyze idea_chars=%d", len(body.idea))
    return await run_star_workflow(body.idea, client, settings)


@router.post("/api/analyze/stream")
async def analyze_stream(
    body: AnalyzeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[HttpA2AClient, Depends(get_a2a_client)],
) -> EventSourceResponse:
    logger.info("POST /api/analyze/stream idea_chars=%d", len(body.idea))

    async def gen():
        try:
            async for ev in run_star_workflow_stream(body.idea, client, settings):
                yield {"data": json.dumps(ev.model_dump())}
        except Exception as e:
            logger.exception("analyze stream failed: %s", e)
            err = {"step": "error", "status": "failed", "detail": str(e)}
            yield {"data": json.dumps(err)}

    return EventSourceResponse(gen())
