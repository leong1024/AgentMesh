"""Extract text from deepagents / LangGraph invoke results."""

from __future__ import annotations

from typing import Any


def last_ai_text(result: dict[str, Any]) -> str:
    """Return concatenated text from the last AI message in graph output."""
    messages = result.get("messages") or []
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or getattr(msg, "role", None)
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, str):
                        parts.append(block)
                    elif isinstance(block, dict) and "text" in block:
                        parts.append(str(block["text"]))
                return "".join(parts)
            return str(content)
    return ""
