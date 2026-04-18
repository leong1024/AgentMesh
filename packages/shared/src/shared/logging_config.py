"""Central logging setup for AgentMesh processes (orchestrator + A2A agents)."""

from __future__ import annotations

import logging
import os
import sys

# Libraries that often ship with WARNING on their loggers; align with LOG_LEVEL so INFO is visible.
_ALIGNED_LOGGERS: tuple[str, ...] = (
    "httpx",
    "httpcore",
    "urllib3",
    "urllib3.connectionpool",
    "langchain",
    "langchain_core",
    "langchain_google_genai",
    "langgraph",
    "langgraph.checkpoint",
    "google_genai",
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "fastapi",
    "sse_starlette",
)


def set_root_log_level_from_env() -> None:
    """Apply ``LOG_LEVEL`` (default ``INFO``) to the root logger and common frameworks.

    Ensures stderr output when no handler exists (e.g. tests). Mirrors the level onto
    third-party loggers that otherwise stay at WARNING and hide INFO lines.
    """
    name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, name, logging.INFO)

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(levelname)s [%(name)s] %(message)s",
            stream=sys.stderr,
        )
    root.setLevel(level)

    for child in _ALIGNED_LOGGERS:
        logging.getLogger(child).setLevel(level)
