"""Thin A2A client: send JSON text, receive artifact text."""

from __future__ import annotations

import logging
import uuid
from typing import Protocol

import httpx
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Part, Role, Task, TextPart
from a2a.utils.artifact import get_artifact_text

logger = logging.getLogger(__name__)


def _task_to_text(task: Task) -> str:
    if not task.artifacts:
        return ""
    parts: list[str] = []
    for art in task.artifacts:
        parts.append(get_artifact_text(art))
    return "\n".join(parts).strip()


class A2AInvoker(Protocol):
    async def invoke(self, base_url: str, payload_json: str) -> str:
        """Send user JSON payload; return agent response text."""


class HttpA2AClient:
    """Uses a2a-sdk ClientFactory (JSON-RPC)."""

    def __init__(self, timeout: httpx.Timeout | None = None) -> None:
        self._timeout = timeout

    async def invoke(self, base_url: str, payload_json: str) -> str:
        logger.info(
            "A2A invoke -> %s payload_chars=%d",
            base_url.rstrip("/"),
            len(payload_json),
        )
        http = httpx.AsyncClient(timeout=self._timeout)
        try:
            cfg = ClientConfig(httpx_client=http, streaming=False)
            client = await ClientFactory.connect(base_url.rstrip("/"), cfg)
        except BaseException:
            await http.aclose()
            raise
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=payload_json))],
        )
        try:
            async for event in client.send_message(msg):
                if isinstance(event, tuple):
                    task, _upd = event
                    text = _task_to_text(task)
                    logger.info(
                        "A2A response from %s artifact_chars=%d",
                        base_url.rstrip("/"),
                        len(text),
                    )
                    return text
                if isinstance(event, Task):
                    text = _task_to_text(event)
                    logger.info(
                        "A2A response from %s artifact_chars=%d",
                        base_url.rstrip("/"),
                        len(text),
                    )
                    return text
        finally:
            await client.close()
        raise RuntimeError(f"A2A agent at {base_url} returned no task result")


class FakeA2AClient:
    """Deterministic client for unit tests."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._responses = responses or {}

    async def invoke(self, base_url: str, payload_json: str) -> str:
        self.calls.append((base_url, payload_json))
        if base_url in self._responses:
            return self._responses[base_url]
        return '{"content":"stub"}'
