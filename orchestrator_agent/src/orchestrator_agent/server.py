"""A2A JSON-RPC server (FastAPI) for the Orchestrator agent."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from shared.a2a_app_factory import build_a2a_fastapi
from shared.a2a_executor import CallbackAgentExecutor
from shared.agent_card import build_agent_card
from shared.env_load import load_local_env
from shared.logging_config import set_root_log_level_from_env
from shared.payloads import AnalyzeRequest, AnalyzeResponse, HealthAgentsResponse
from sse_starlette.sse import EventSourceResponse

from orchestrator_agent.deep_agent import run_orchestrator
from orchestrator_agent.settings import Settings
from orchestrator_agent.workflow import (
    run_analyze_workflow,
    run_analyze_workflow_stream,
    run_chat_workflow,
    run_chat_workflow_stream,
)
from shared.payloads import ChatMessageRequest, ChatMessageResponse


def create_app() -> FastAPI:
    load_local_env()
    set_root_log_level_from_env()
    settings = Settings()
    logging.getLogger(__name__).info(
        "orchestrator agent listening (LOG_LEVEL=%s)",
        os.environ.get("LOG_LEVEL", "INFO"),
    )
    public_url = os.environ.get(
        "ORCHESTRATOR_AGENT_PUBLIC_URL",
        f"http://127.0.0.1:{os.environ.get('ORCHESTRATOR_AGENT_PORT', '8003')}",
    )
    card = build_agent_card(
        name="AgentMesh Orchestrator",
        description="Coordinates research and critique, then produces final Markdown report.",
        skill_id="orchestrator",
        skill_name="orchestrate_analysis",
        public_url=public_url,
    )
    app = build_a2a_fastapi(card, CallbackAgentExecutor(run_orchestrator))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health/agents", response_model=HealthAgentsResponse)
    async def health_agents() -> HealthAgentsResponse:
        async def probe(url: str) -> bool:
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(settings.http_timeout_seconds)
                ) as client:
                    r = await client.get(f"{url.rstrip('/')}/.well-known/agent-card.json")
                return r.status_code == 200
            except Exception:
                return False

        return HealthAgentsResponse(
            research=await probe(settings.research_a2a_url),
            critic=await probe(settings.critic_a2a_url),
        )

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
        return await run_analyze_workflow(body.idea, settings)

    @app.post("/api/analyze/stream")
    async def analyze_stream(body: AnalyzeRequest) -> EventSourceResponse:
        async def gen():
            try:
                async for ev in run_analyze_workflow_stream(body.idea, settings):
                    yield {"data": json.dumps(ev.model_dump())}
            except Exception as e:
                err = {"step": "error", "status": "failed", "detail": str(e)}
                yield {"data": json.dumps(err)}

        return EventSourceResponse(gen())

    @app.post("/api/chat", response_model=ChatMessageResponse)
    async def chat(body: ChatMessageRequest) -> ChatMessageResponse:
        return await run_chat_workflow(
            body.message,
            settings,
            session_id=body.session_id,
            thread_id=body.thread_id,
        )

    @app.post("/api/chat/stream")
    async def chat_stream(body: ChatMessageRequest) -> EventSourceResponse:
        async def gen():
            try:
                async for ev in run_chat_workflow_stream(
                    body.message,
                    settings,
                    session_id=body.session_id,
                    thread_id=body.thread_id,
                ):
                    yield {"data": json.dumps(ev.model_dump())}
            except Exception as e:
                err = {
                    "event": "error",
                    "session_id": body.session_id or "",
                    "thread_id": body.thread_id or "",
                    "detail": str(e),
                }
                yield {"data": json.dumps(err)}

        return EventSourceResponse(gen())

    if settings.static_dir:
        static_path = Path(settings.static_dir)
        if static_path.is_dir():
            assets = static_path / "assets"
            if assets.is_dir():
                app.mount("/assets", StaticFiles(directory=assets), name="assets")

            @app.get("/")
            async def spa_index():
                index = static_path / "index.html"
                if index.is_file():
                    return FileResponse(index)
                return {"detail": "Run frontend build first"}

    return app


def main() -> None:
    settings = Settings()
    host = os.environ.get("ORCHESTRATOR_AGENT_HOST", settings.api_host)
    port = int(os.environ.get("ORCHESTRATOR_AGENT_PORT", str(settings.api_port)))
    uvicorn.run(
        "orchestrator_agent.server:create_app",
        factory=True,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
