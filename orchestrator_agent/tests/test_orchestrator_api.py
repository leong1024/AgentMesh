from __future__ import annotations

from fastapi.testclient import TestClient
from orchestrator_agent.server import create_app
from shared.payloads import SynthesizerOut


def test_orchestrator_analyze_endpoint(monkeypatch) -> None:
    async def fake_run(*_args, **_kwargs) -> SynthesizerOut:
        return SynthesizerOut(executive_summary="", report="# OK")

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_for_idea", fake_run)
    app = create_app()
    with TestClient(app) as client:
        r = client.post("/api/analyze", json={"idea": "My app"})
    assert r.status_code == 200
    assert r.json()["report"] == "# OK"


def test_orchestrator_analyze_validation(monkeypatch) -> None:
    async def fake_run(*_args, **_kwargs) -> SynthesizerOut:
        return SynthesizerOut(executive_summary="", report="# OK")

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_for_idea", fake_run)
    app = create_app()
    with TestClient(app) as client:
        r = client.post("/api/analyze", json={"idea": ""})
    assert r.status_code == 422


def test_orchestrator_chat_endpoint(monkeypatch) -> None:
    async def fake_chat(*_args, **_kwargs) -> str:
        return "Hello from orchestrator"

    monkeypatch.setattr("orchestrator_agent.workflow.run_orchestrator_chat", fake_chat)
    app = create_app()
    with TestClient(app) as client:
        r = client.post("/api/chat", json={"message": "hi", "session_id": "s1", "thread_id": "t1"})
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == "Hello from orchestrator"
    assert body["session_id"] == "s1"
    assert body["thread_id"] == "t1"
