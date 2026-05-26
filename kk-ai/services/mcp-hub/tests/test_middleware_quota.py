"""Tests for QuotaMiddleware."""

from fastapi.testclient import TestClient


def test_quota_exempt_paths(client: TestClient) -> None:
    """Test that exempt paths bypass quota checking."""
    response = client.get("/health")
    assert response.status_code == 200


def test_quota_without_api_key(client: TestClient) -> None:
    """Test that protected paths require API key (auth before quota)."""
    response = client.get("/mcp-a/api/test")
    assert response.status_code == 401


def test_quota_with_valid_key_no_rule_allows(client: TestClient) -> None:
    """Test that requests pass quota check when no quota rule exists."""
    response = client.get(
        "/mcp-a/api/test",
        headers={"X-API-Key": "kk-admin-key"},
    )
    # No quota rule for admin project -> allowed
    assert response.status_code != 429


def test_quota_api_exempt_from_middleware(client: TestClient) -> None:
    """Test that quota API paths are accessible without auth."""
    response = client.get("/api/v1/quota/rules")
    assert response.status_code == 200
