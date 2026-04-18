"""Orchestrator: A2A Research + Critic, then in-process Deep Agent for final synthesis."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from shared.graph_output import last_ai_text
from shared.model_factory import DEFAULT_GEMINI_MODEL_SPEC, gemini_chat_model
from shared.payloads import (
    AnalyzeResponse,
    CriticIn,
    CriticOut,
    ResearchIn,
    ResearchOut,
    StepOutputs,
    StreamEvent,
    SynthesizerOut,
)
from shared.prompts import ORCHESTRATOR_SYSTEM

from orchestrator.a2a_client import A2AInvoker
from orchestrator.settings import Settings

logger = logging.getLogger(__name__)


def _preview_idea(idea: str, max_len: int = 160) -> str:
    one = idea.replace("\n", " ").strip()
    if len(one) <= max_len:
        return one
    return one[: max_len - 3] + "..."


def _final_report_from_synthesis(raw: str) -> str:
    synth = SynthesizerOut.parse_loose(raw)
    if synth.report.strip():
        return synth.report.strip()
    if synth.executive_summary.strip():
        return synth.executive_summary.strip()
    return json.dumps(synth.model_dump(), indent=2)


def build_orchestration_agent(settings: Settings):
    spec = (settings.orchestrator_model or "").strip() or DEFAULT_GEMINI_MODEL_SPEC
    model = gemini_chat_model(spec)
    return create_deep_agent(
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM,
        tools=(),
    )


async def synthesize_final_report(
    idea: str,
    research: ResearchOut,
    critic: CriticOut,
    settings: Settings,
) -> str:
    """Run the orchestrator deep agent (no tools) to merge idea + research + critique."""
    agent = build_orchestration_agent(settings)
    payload = {
        "idea": idea,
        "research": research.model_dump(),
        "critique": critic.model_dump(),
    }
    prompt = (
        "Write the final product analysis. Input JSON:\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Respond with the JSON object only, as specified in your system instructions."
    )
    out = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    text = last_ai_text(out)
    return _final_report_from_synthesis(text)


async def run_analyze_workflow(
    idea: str,
    client: A2AInvoker,
    settings: Settings,
) -> AnalyzeResponse:
    r_in = ResearchIn(idea=idea)
    r_raw = await client.invoke(settings.research_a2a_url, r_in.model_dump_json())
    research = ResearchOut.parse_loose(r_raw)

    c_in = CriticIn(idea=idea, research=research.model_dump())
    c_raw = await client.invoke(settings.critic_a2a_url, c_in.model_dump_json())
    critic = CriticOut.parse_loose(c_raw)

    report = await synthesize_final_report(idea, research, critic, settings)

    return AnalyzeResponse(
        report=report,
        steps=StepOutputs(research=research, critic=critic),
    )


async def run_analyze_workflow_stream(
    idea: str,
    client: A2AInvoker,
    settings: Settings,
) -> AsyncIterator[StreamEvent]:
    t_run = time.perf_counter()
    logger.info(
        "workflow stream start idea_chars=%d preview=%r",
        len(idea),
        _preview_idea(idea),
    )

    ev0 = StreamEvent(step="research", status="started", detail=None)
    logger.info("sse yield step=%s status=%s", ev0.step, ev0.status)
    yield ev0
    r_in = ResearchIn(idea=idea)
    t0 = time.perf_counter()
    r_raw = await client.invoke(settings.research_a2a_url, r_in.model_dump_json())
    research = ResearchOut.parse_loose(r_raw)
    logger.info(
        "research done in %.2fs response_chars=%d",
        time.perf_counter() - t0,
        len(r_raw),
    )
    ev1 = StreamEvent(step="research", status="completed", detail=None)
    logger.info("sse yield step=%s status=%s", ev1.step, ev1.status)
    yield ev1

    ev2 = StreamEvent(step="critic", status="started", detail=None)
    logger.info("sse yield step=%s status=%s", ev2.step, ev2.status)
    yield ev2
    t0 = time.perf_counter()
    c_in = CriticIn(idea=idea, research=research.model_dump())
    c_raw = await client.invoke(settings.critic_a2a_url, c_in.model_dump_json())
    critic = CriticOut.parse_loose(c_raw)
    logger.info(
        "critic done in %.2fs response_chars=%d",
        time.perf_counter() - t0,
        len(c_raw),
    )
    ev3 = StreamEvent(step="critic", status="completed", detail=None)
    logger.info("sse yield step=%s status=%s", ev3.step, ev3.status)
    yield ev3

    ev4 = StreamEvent(step="report", status="started", detail=None)
    logger.info("sse yield step=%s status=%s", ev4.step, ev4.status)
    yield ev4
    t0 = time.perf_counter()
    report = await synthesize_final_report(idea, research, critic, settings)
    logger.info(
        "orchestrator synthesis done in %.2fs report_chars=%d",
        time.perf_counter() - t0,
        len(report),
    )
    ev5 = StreamEvent(step="report", status="completed", detail=None)
    logger.info("sse yield step=%s status=%s", ev5.step, ev5.status)
    yield ev5

    logger.info(
        "workflow stream complete total_s=%.2fs report_chars=%d",
        time.perf_counter() - t_run,
        len(report),
    )
    ev6 = StreamEvent(step="complete", status="done", report=report)
    logger.info(
        "sse yield step=%s status=%s report_chars=%d",
        ev6.step,
        ev6.status,
        len(report),
    )
    yield ev6
