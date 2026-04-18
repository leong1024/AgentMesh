"""Optional LLM smoke — skipped unless RUN_LLM_TESTS=1."""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_llm,
]


@pytest.mark.asyncio
async def test_run_research_live() -> None:
    if os.environ.get("RUN_LLM_TESTS") != "1":
        pytest.skip("RUN_LLM_TESTS not set")
    from agent_research.deep_agent import run_research

    out = await run_research('{"idea":"A simple todo app."}')
    assert len(out) > 0
