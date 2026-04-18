"""API tests with dependency overrides."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from orchestrator.dependencies import get_a2a_client, get_settings
from orchestrator.main import create_app
from orchestrator.settings import Settings


class SeqFakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.i = 0

    async def invoke(self, base_url: str, payload_json: str) -> str:
        out = self.outputs[self.i]
        self.i += 1
        return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    async def fake_synth(idea, research, critic, settings) -> str:
        return "# OK"

    monkeypatch.setattr(
        "orchestrator.deep_workflow.synthesize_final_report",
        fake_synth,
    )
    app = create_app()
    fake = SeqFakeClient(
        [
            '{"assumptions":[],"market_context":"","open_questions":[]}',
            '{"risks":[],"flaws":[],"investor_concerns":[]}',
        ]
    )
    app.dependency_overrides[get_a2a_client] = lambda: fake
    app.dependency_overrides[get_settings] = lambda: Settings()
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


def test_analyze_endpoint(client: TestClient) -> None:
    r = client.post("/api/analyze", json={"idea": "My app"})
    assert r.status_code == 200
    body = r.json()
    assert body["report"] == "# OK"


def test_analyze_validation(client: TestClient) -> None:
    r = client.post("/api/analyze", json={"idea": ""})
    assert r.status_code == 422
