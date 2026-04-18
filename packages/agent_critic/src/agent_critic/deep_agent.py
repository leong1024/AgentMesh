"""Deep Agents graph for the Critic role."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from shared.graph_output import last_ai_text
from shared.model_factory import DEFAULT_GROQ_MODEL_SPEC, groq_chat_model
from shared.payloads import CriticIn
from shared.prompts import CRITIC_SYSTEM


def _model():
    spec = os.environ.get("CRITIC_MODEL", DEFAULT_GROQ_MODEL_SPEC)
    return groq_chat_model(spec)


def build_critic_graph():
    return create_deep_agent(
        model=_model(),
        system_prompt=CRITIC_SYSTEM,
        tools=(),
    )


async def run_critic(user_payload_json: str) -> str:
    payload = CriticIn.model_validate_json(user_payload_json)
    agent = build_critic_graph()
    prompt = (
        "Critique this idea using the prior research. Input JSON:\n"
        f"{payload.model_dump_json(indent=2)}\n\n"
        "Respond with the JSON object only, as specified in your system instructions."
    )
    out = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    return last_ai_text(out)
