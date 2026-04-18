"""Deep Agents graph for the Research role."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from shared.graph_output import last_ai_text
from shared.model_factory import DEFAULT_GROQ_MODEL_SPEC, groq_chat_model
from shared.payloads import ResearchIn
from shared.prompts import RESEARCH_SYSTEM


def _model():
    spec = os.environ.get("RESEARCH_MODEL", DEFAULT_GROQ_MODEL_SPEC)
    return groq_chat_model(spec)


def build_research_graph():
    """Compiled LangGraph agent (research — no web tools)."""
    return create_deep_agent(
        model=_model(),
        system_prompt=RESEARCH_SYSTEM,
        tools=(),
    )


async def run_research(user_payload_json: str) -> str:
    """Parse `ResearchIn` JSON, invoke agent, return model text (JSON string)."""
    payload = ResearchIn.model_validate_json(user_payload_json)
    agent = build_research_graph()
    prompt = (
        "Analyze this product idea. Input JSON:\n"
        f"{payload.model_dump_json(indent=2)}\n\n"
        "Respond with the JSON object only, as specified in your system instructions."
    )
    out = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    return last_ai_text(out)
