"""Build LangChain chat models for Deep Agents — Groq API only."""

from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

# Default Groq model id (LangChain unified string). Override per role via *_MODEL env.
DEFAULT_GROQ_MODEL_SPEC = "groq:llama-3.3-70b-versatile"


def groq_chat_model(model_spec: str) -> BaseChatModel:
    """Return a Groq-backed chat model via ``init_chat_model``.

    ``model_spec`` must be a LangChain unified id starting with ``groq:`` (for example
    ``groq:llama-3.3-70b-versatile``). Requires ``GROQ_API_KEY`` and ``langchain-groq``.
    """
    s = model_spec.strip()
    if not s:
        raise ValueError("Groq model spec must not be empty")
    if not s.startswith("groq:"):
        raise ValueError(
            "Only Groq models are supported. Set RESEARCH_MODEL / CRITIC_MODEL / "
            "SYNTHESIZER_MODEL to a unified id starting with 'groq:', for example "
            f"{DEFAULT_GROQ_MODEL_SPEC!r}. Got: {s!r}"
        )
    return init_chat_model(s)
