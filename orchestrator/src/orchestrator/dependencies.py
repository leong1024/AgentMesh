"""FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends

from orchestrator.a2a_client import HttpA2AClient
from orchestrator.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_http_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[httpx.AsyncClient]:
    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


def get_a2a_client(
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> HttpA2AClient:
    return HttpA2AClient(http_client)
