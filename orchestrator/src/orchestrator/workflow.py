"""Star workflow: Research → Critic → Synthesizer."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from shared.payloads import (
    AnalyzeResponse,
    CriticIn,
    CriticOut,
    ResearchIn,
    ResearchOut,
    StepOutputs,
    StreamEvent,
    SynthesizerIn,
    SynthesizerOut,
)

from orchestrator.a2a_client import A2AInvoker
from orchestrator.settings import Settings


def _final_report(synth: SynthesizerOut) -> str:
    if synth.report.strip():
        return synth.report.strip()
    if synth.executive_summary.strip():
        return synth.executive_summary.strip()
    return json.dumps(synth.model_dump(), indent=2)


async def run_star_workflow(idea: str, client: A2AInvoker, settings: Settings) -> AnalyzeResponse:
    r_in = ResearchIn(idea=idea)
    r_raw = await client.invoke(settings.research_a2a_url, r_in.model_dump_json())
    research = ResearchOut.parse_loose(r_raw)

    c_in = CriticIn(idea=idea, research=research.model_dump())
    c_raw = await client.invoke(settings.critic_a2a_url, c_in.model_dump_json())
    critic = CriticOut.parse_loose(c_raw)

    s_in = SynthesizerIn(
        idea=idea,
        research=research.model_dump(),
        critique=critic.model_dump(),
    )
    s_raw = await client.invoke(settings.synthesizer_a2a_url, s_in.model_dump_json())
    synthesizer = SynthesizerOut.parse_loose(s_raw)

    return AnalyzeResponse(
        report=_final_report(synthesizer),
        steps=StepOutputs(
            research=research,
            critic=critic,
            synthesizer=synthesizer,
        ),
    )


async def run_star_workflow_stream(
    idea: str,
    client: A2AInvoker,
    settings: Settings,
) -> AsyncIterator[StreamEvent]:
    yield StreamEvent(step="research", status="started", detail=None)
    r_in = ResearchIn(idea=idea)
    r_raw = await client.invoke(settings.research_a2a_url, r_in.model_dump_json())
    research = ResearchOut.parse_loose(r_raw)
    yield StreamEvent(step="research", status="completed", detail=None)

    yield StreamEvent(step="critic", status="started", detail=None)
    c_in = CriticIn(idea=idea, research=research.model_dump())
    c_raw = await client.invoke(settings.critic_a2a_url, c_in.model_dump_json())
    critic = CriticOut.parse_loose(c_raw)
    yield StreamEvent(step="critic", status="completed", detail=None)

    yield StreamEvent(step="synthesizer", status="started", detail=None)
    s_in = SynthesizerIn(
        idea=idea,
        research=research.model_dump(),
        critique=critic.model_dump(),
    )
    s_raw = await client.invoke(settings.synthesizer_a2a_url, s_in.model_dump_json())
    synthesizer = SynthesizerOut.parse_loose(s_raw)
    yield StreamEvent(step="synthesizer", status="completed", detail=None)

    report = _final_report(synthesizer)
    yield StreamEvent(step="complete", status="done", report=report)
