"""Build LangChain chat models for Deep Agents — Google Gemini (Gen AI) API."""

from __future__ import annotations

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

# LangChain unified id (see init_chat_model). Override per role via *_MODEL env.
DEFAULT_GEMINI_MODEL_SPEC = "google_genai:gemma-4-31b-it"


def _ensure_google_api_key() -> None:
    """LangChain Google Gen AI reads ``GOOGLE_API_KEY``; also accept ``GEMINI_API_KEY``."""
    if os.environ.get("GOOGLE_API_KEY"):
        return
    gemini = os.environ.get("GEMINI_API_KEY")
    if gemini:
        os.environ["GOOGLE_API_KEY"] = gemini


def gemini_chat_model(model_spec: str) -> BaseChatModel:
    """Return a Google Gen AI chat model via ``init_chat_model``.

    ``model_spec`` must start with ``google_genai:`` (for example
    ``google_genai:gemma-4-31b-it``). Set ``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``.
    Requires ``langchain-google-genai``.
    """
    _ensure_google_api_key()
    s = model_spec.strip()
    if not s:
        raise ValueError("Gemini model spec must not be empty")
    if not s.startswith("google_genai:"):
        raise ValueError(
            "Only Google Gen AI models are supported. Set RESEARCH_MODEL / "
            "CRITIC_MODEL / SYNTHESIZER_MODEL to a unified id starting with "
            f"'google_genai:', for example {DEFAULT_GEMINI_MODEL_SPEC!r}. Got: {s!r}"
        )
    return init_chat_model(s)
