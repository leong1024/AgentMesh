"""Tune root log level for AgentMesh processes (orchestrator + agents)."""

from __future__ import annotations

import logging
import os


def set_root_log_level_from_env() -> None:
    """Apply ``LOG_LEVEL`` (default INFO) to the root logger so app loggers emit to the console."""
    name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, name, logging.INFO)
    logging.getLogger().setLevel(level)
