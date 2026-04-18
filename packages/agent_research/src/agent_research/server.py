"""A2A JSON-RPC server (FastAPI) for the Research agent."""

from __future__ import annotations

import logging
import os

import uvicorn
from shared.a2a_app_factory import build_a2a_fastapi
from shared.a2a_executor import CallbackAgentExecutor
from shared.agent_card import build_agent_card
from shared.env_load import load_local_env
from shared.logging_config import set_root_log_level_from_env

from agent_research.deep_agent import run_research


def create_app():
    load_local_env()
    set_root_log_level_from_env()
    logging.getLogger(__name__).info(
        "research agent listening (LOG_LEVEL=%s)",
        os.environ.get("LOG_LEVEL", "INFO"),
    )
    public_url = os.environ.get(
        "RESEARCH_PUBLIC_URL",
        f"http://127.0.0.1:{os.environ.get('RESEARCH_PORT', '8001')}",
    )
    card = build_agent_card(
        name="AgentMesh Research",
        description="Expands a product idea into assumptions and context (no web browsing).",
        skill_id="research",
        skill_name="research_analysis",
        public_url=public_url,
    )
    return build_a2a_fastapi(card, CallbackAgentExecutor(run_research))


def main() -> None:
    host = os.environ.get("RESEARCH_HOST", "0.0.0.0")
    port = int(os.environ.get("RESEARCH_PORT", "8001"))
    uvicorn.run(
        "agent_research.server:create_app",
        factory=True,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
