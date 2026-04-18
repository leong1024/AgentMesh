"""Model factory — Google Gen AI (Gemini API)."""

from unittest.mock import patch

import pytest
from shared.model_factory import DEFAULT_GEMINI_MODEL_SPEC, gemini_chat_model


def test_default_spec_is_google_genai() -> None:
    assert DEFAULT_GEMINI_MODEL_SPEC.startswith("google_genai:")


def test_non_google_genai_prefix_raises() -> None:
    with pytest.raises(ValueError, match="Only Google Gen AI"):
        gemini_chat_model("groq:llama-3.1-70b-versatile")


def test_empty_spec_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        gemini_chat_model("   ")


def test_google_genai_uses_init_chat_model() -> None:
    fake_model = object()
    with patch(
        "shared.model_factory.init_chat_model",
        return_value=fake_model,
    ) as mock:
        out = gemini_chat_model("google_genai:gemma-4-31b-it")
        mock.assert_called_once_with("google_genai:gemma-4-31b-it")
        assert out is fake_model
