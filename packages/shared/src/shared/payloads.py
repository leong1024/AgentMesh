"""Pydantic payloads for orchestrator API and agent step I/O."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_IDEA_CHARS = 32_000


class AnalyzeRequest(BaseModel):
    """POST /api/analyze body."""

    idea: str = Field(..., min_length=1, max_length=MAX_IDEA_CHARS)


class ResearchIn(BaseModel):
    idea: str


class ResearchOut(BaseModel):
    assumptions: list[str] = Field(default_factory=list)
    market_context: str = ""
    open_questions: list[str] = Field(default_factory=list)
    content: str | None = None

    @classmethod
    def parse_loose(cls, raw: str) -> ResearchOut:
        raw = raw.strip()
        if not raw:
            return cls()
        try:
            return cls.model_validate_json(raw)
        except Exception:
            return cls(content=raw)


class CriticIn(BaseModel):
    idea: str
    research: Any


class CriticOut(BaseModel):
    risks: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)
    investor_concerns: list[str] = Field(default_factory=list)
    content: str | None = None

    @classmethod
    def parse_loose(cls, raw: str) -> CriticOut:
        raw = raw.strip()
        if not raw:
            return cls()
        try:
            return cls.model_validate_json(raw)
        except Exception:
            return cls(content=raw)


class SynthesizerIn(BaseModel):
    idea: str
    research: Any
    critique: Any


class SynthesizerOut(BaseModel):
    executive_summary: str = ""
    sections: dict[str, Any] = Field(default_factory=dict)
    report: str = ""

    @classmethod
    def parse_loose(cls, raw: str) -> SynthesizerOut:
        raw = raw.strip()
        if not raw:
            return cls(report="")
        try:
            return cls.model_validate_json(raw)
        except Exception:
            return cls(report=raw)


class StepOutputs(BaseModel):
    research: ResearchOut
    critic: CriticOut
    synthesizer: SynthesizerOut


class AnalyzeResponse(BaseModel):
    report: str
    steps: StepOutputs


class StreamEvent(BaseModel):
    """SSE payload for /api/analyze/stream."""

    step: str
    status: str
    detail: str | None = None
    report: str | None = None


class HealthAgentsResponse(BaseModel):
    research: bool
    critic: bool
    synthesizer: bool

    @field_validator("research", "critic", "synthesizer", mode="before")
    @classmethod
    def _coerce_bool(cls, v: Any) -> bool:
        return bool(v)
