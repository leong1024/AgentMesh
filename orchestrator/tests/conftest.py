"""Pytest fixtures."""

from __future__ import annotations

import pytest
from orchestrator.settings import Settings


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        research_a2a_url="http://127.0.0.1:8001",
        critic_a2a_url="http://127.0.0.1:8002",
    )
