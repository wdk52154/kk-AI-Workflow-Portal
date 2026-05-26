"""Tests for RateLimitMiddleware."""

from fastapi.testclient import TestClient


def test_rate_limit_exempt_paths(client: TestClient) -> None:
    """Test that exempt paths bypass rate limiting."""
    response = client.get("/health")
    assert response.status_code == 200


def test_rate_limit_without_api_key(client: TestClient) -> None:
    """Test that protected paths require API key (auth before rate limit)."""
    response = client.get("/mcp-a/api/test")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "UNAUTHORIZED"


def test_rate_limit_with_valid_key(client: TestClient) -> None:
    """Test that valid API key passes rate limiting."""
    response = client.get(
        "/mcp-a/api/test",
        headers={"X-API-Key": "kk-admin-key"},
    )
    # Should be 404 (service not found) not 429 (rate limited)
    assert response.status_code != 429


def test_rate_limit_trace_header_present(client: TestClient) -> None:
    """Test that trace_id header is present in responses."""
    response = client.get("/health")
    assert "X-Trace-Id" in response.headers
