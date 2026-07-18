"""The API health endpoint is the Milestone 0 smoke check (curl -> 200)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_payload_reports_ok_and_mock():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    # First boot must run mocked so no API key is required.
    assert body["llm_mock"] is True
