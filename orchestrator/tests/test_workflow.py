"""Unit tests for analyze workflow with a fake A2A client."""

from __future__ import annotations

import pytest
from orchestrator.workflow import run_star_workflow


class SeqFakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.i = 0
        self.calls: list[tuple[str, str]] = []

    async def invoke(self, base_url: str, payload_json: str) -> str:
        self.calls.append((base_url, payload_json))
        out = self.outputs[self.i]
        self.i += 1
        return out


@pytest.mark.asyncio
async def test_star_order_and_threading(test_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_synth(
        idea: str,
        research,
        critic,
        settings,
    ) -> str:
        return "# Final"

    monkeypatch.setattr(
        "orchestrator.deep_workflow.synthesize_final_report",
        fake_synth,
    )
    fake = SeqFakeClient(
        [
            '{"assumptions":["a1"],"market_context":"mc","open_questions":["q"]}',
            '{"risks":["r1"],"flaws":[],"investor_concerns":[]}',
        ]
    )
    result = await run_star_workflow("idea text", fake, test_settings)
    assert len(fake.calls) == 2
    assert "idea text" in fake.calls[0][1]
    assert result.report == "# Final"
    assert result.steps.research.assumptions == ["a1"]
    assert result.steps.critic.risks == ["r1"]


@pytest.mark.asyncio
async def test_star_falls_back_to_summary(test_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_synth(
        idea: str,
        research,
        critic,
        settings,
    ) -> str:
        return "only"

    monkeypatch.setattr(
        "orchestrator.deep_workflow.synthesize_final_report",
        fake_synth,
    )
    fake = SeqFakeClient(
        [
            "{}",
            "{}",
        ]
    )
    result = await run_star_workflow("x", fake, test_settings)
    assert result.report == "only"
