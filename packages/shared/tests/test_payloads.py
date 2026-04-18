import pytest
from pydantic import ValidationError
from shared.payloads import (
    MAX_IDEA_CHARS,
    AnalyzeRequest,
    CriticOut,
    ResearchOut,
    SynthesizerOut,
)


def test_analyze_request_round_trip() -> None:
    body = AnalyzeRequest(idea="A note app for chefs.")
    d = body.model_dump()
    assert AnalyzeRequest.model_validate(d).idea == body.idea


def test_analyze_request_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(idea="")


def test_analyze_request_rejects_too_long() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(idea="x" * (MAX_IDEA_CHARS + 1))


def test_research_parse_loose_json() -> None:
    raw = '{"assumptions":["a"],"market_context":"m","open_questions":["q"]}'
    r = ResearchOut.parse_loose(raw)
    assert r.assumptions == ["a"]
    assert r.market_context == "m"


def test_research_parse_loose_non_json() -> None:
    r = ResearchOut.parse_loose("just some prose")
    assert r.content == "just some prose"


def test_critic_parse_loose() -> None:
    o = CriticOut.parse_loose('{"risks":["r"],"flaws":[],"investor_concerns":[]}')
    assert o.risks == ["r"]


def test_synthesizer_report_fallback() -> None:
    s = SynthesizerOut.parse_loose("# Hello\n\nBody")
    assert "# Hello" in s.report
