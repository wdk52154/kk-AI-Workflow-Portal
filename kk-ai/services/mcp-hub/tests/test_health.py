"""Tests for health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint returns expected structure."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "mcp-hub"
    assert data["version"] == "0.1.0"
    assert data["status"] in ["ok", "degraded"]
    assert "redis_connected" in data
    assert "upstream_services" in data


def test_health_trace_header(client: TestClient) -> None:
    """Test health check includes trace_id header."""
    response = client.get("/health")
    assert "X-Trace-Id" in response.headers
    assert len(response.headers["X-Trace-Id"]) > 0
