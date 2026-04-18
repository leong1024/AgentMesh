"""Thin A2A client: send JSON text, receive artifact text."""

from __future__ import annotations

import uuid
from typing import Protocol

import httpx
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Part, Role, Task, TextPart
from a2a.utils.artifact import get_artifact_text


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
    """Uses a2a-sdk ClientFactory (JSON-RPC) with a shared httpx client."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def invoke(self, base_url: str, payload_json: str) -> str:
        cfg = ClientConfig(httpx_client=self._http, streaming=False)
        client = await ClientFactory.connect(base_url.rstrip("/"), cfg)
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=payload_json))],
        )
        try:
            async for event in client.send_message(msg):
                if isinstance(event, tuple):
                    task, _upd = event
                    return _task_to_text(task)
                if isinstance(event, Task):
                    return _task_to_text(event)
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
