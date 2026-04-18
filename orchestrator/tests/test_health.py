"""Health endpoint."""

from fastapi.testclient import TestClient
from orchestrator.main import create_app


def test_health() -> None:
    app = create_app()
    with TestClient(app) as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
