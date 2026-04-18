"""Resolve Deep Agents `model=` from env strings (Ollama IDs, Groq via init_chat_model, etc.)."""

from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel


def resolve_deepagent_model(model_spec: str) -> BaseChatModel | str:
    """Return a chat model instance or a provider string for `create_deep_agent`.

    - ``groq:...`` — ``init_chat_model`` (requires ``GROQ_API_KEY`` and ``langchain-groq``).
    - Anything else — passed through (e.g. ``ollama:llama3.2``, ``openai:gpt-4o``).
    """
    s = model_spec.strip()
    if not s:
        raise ValueError("model_spec must not be empty")

    if s.startswith("groq:"):
        return init_chat_model(s)

    return s
