"""Tests for rate limit middleware."""

from fastapi.testclient import TestClient


def test_rate_limit_exempt_paths(client: TestClient) -> None:
    """Test that exempt paths bypass rate limiting."""
    # Health check should work without API key
    response = client.get("/health")
    assert response.status_code == 200


def test_rate_limit_without_api_key(client: TestClient) -> None:
    """Test that protected paths require API key."""
    response = client.get("/mcp-a/api/test")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "UNAUTHORIZED"
