"""A2A JSON-RPC server (FastAPI) for the Synthesizer agent."""

from __future__ import annotations

import logging
import os

import uvicorn
from shared.a2a_app_factory import build_a2a_fastapi
from shared.a2a_executor import CallbackAgentExecutor
from shared.agent_card import build_agent_card
from shared.env_load import load_local_env
from shared.logging_config import set_root_log_level_from_env

from agent_synthesizer.deep_agent import run_synthesizer


def create_app():
    load_local_env()
    set_root_log_level_from_env()
    logging.getLogger(__name__).info(
        "synthesizer agent listening (LOG_LEVEL=%s)",
        os.environ.get("LOG_LEVEL", "INFO"),
    )
    public_url = os.environ.get(
        "SYNTHESIZER_PUBLIC_URL",
        f"http://127.0.0.1:{os.environ.get('SYNTHESIZER_PORT', '8003')}",
    )
    card = build_agent_card(
        name="AgentMesh Synthesizer",
        description="Merges research and critique into one Markdown report.",
        skill_id="synthesizer",
        skill_name="synthesize_report",
        public_url=public_url,
    )
    return build_a2a_fastapi(card, CallbackAgentExecutor(run_synthesizer))


def main() -> None:
    host = os.environ.get("SYNTHESIZER_HOST", "0.0.0.0")
    port = int(os.environ.get("SYNTHESIZER_PORT", "8003"))
    uvicorn.run(
        "agent_synthesizer.server:create_app",
        factory=True,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
