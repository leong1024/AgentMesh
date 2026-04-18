"""Model resolution for Deep Agents."""

from unittest.mock import patch

from shared.model_factory import resolve_deepagent_model


def test_passthrough_ollama_string() -> None:
    m = resolve_deepagent_model("ollama:llama3.2")
    assert m == "ollama:llama3.2"


def test_passthrough_openai_style_string() -> None:
    assert resolve_deepagent_model("openai:gpt-4o-mini") == "openai:gpt-4o-mini"


def test_groq_uses_init_chat_model() -> None:
    fake_model = object()
    with patch(
        "shared.model_factory.init_chat_model",
        return_value=fake_model,
    ) as mock:
        out = resolve_deepagent_model("groq:llama-3.1-70b-versatile")
        mock.assert_called_once_with("groq:llama-3.1-70b-versatile")
        assert out is fake_model
