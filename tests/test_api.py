from __future__ import annotations

from fastapi.testclient import TestClient

from bridgewatch.api import app
from bridgewatch.config import Settings
from bridgewatch import api as api_module
from bridgewatch import auth as auth_module


def test_dashboard_contract(tmp_path, monkeypatch):
    settings = Settings(database_path=tmp_path / "api.db", api_key="test-key", base_retry_seconds=0)
    monkeypatch.setattr(api_module, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    client = TestClient(app)

    unauthorized = client.post("/api/ingest/sample")
    assert unauthorized.status_code == 401

    ingest = client.post("/api/ingest/sample", headers={"X-API-Key": "test-key"})
    assert ingest.status_code == 200
    run = client.post("/api/integrations/run", headers={"X-API-Key": "test-key"})
    assert run.status_code == 200

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert {"latest_run", "events_by_status", "incidents", "findings", "retries"} <= set(body)
