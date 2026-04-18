"""Model factory — Groq-only."""

from unittest.mock import patch

import pytest
from shared.model_factory import DEFAULT_GROQ_MODEL_SPEC, groq_chat_model


def test_default_spec_is_groq() -> None:
    assert DEFAULT_GROQ_MODEL_SPEC.startswith("groq:")


def test_non_groq_prefix_raises() -> None:
    with pytest.raises(ValueError, match="Only Groq"):
        groq_chat_model("ollama:llama3.2")


def test_empty_spec_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        groq_chat_model("   ")


def test_groq_uses_init_chat_model() -> None:
    fake_model = object()
    with patch(
        "shared.model_factory.init_chat_model",
        return_value=fake_model,
    ) as mock:
        out = groq_chat_model("groq:llama-3.1-70b-versatile")
        mock.assert_called_once_with("groq:llama-3.1-70b-versatile")
        assert out is fake_model
