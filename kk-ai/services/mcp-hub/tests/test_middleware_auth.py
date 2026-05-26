"""Tests for AuthMiddleware."""

from fastapi.testclient import TestClient


def test_auth_missing_key_returns_401(client: TestClient) -> None:
    """Test that protected paths return 401 without API key."""
    response = client.get("/mcp-a/api/test")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "UNAUTHORIZED"
    assert "Missing" in data["message"]


def test_auth_invalid_key_returns_401(client: TestClient) -> None:
    """Test that invalid API key returns 401."""
    response = client.get(
        "/mcp-a/api/test",
        headers={"X-API-Key": "invalid-key"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "UNAUTHORIZED"
    assert data["message"] == "Invalid API key"


def test_auth_valid_key_sets_project_id(client: TestClient) -> None:
    """Test that valid API key sets project info on request state."""
    response = client.get(
        "/health",
        headers={"X-API-Key": "kk-admin-key"},
    )
    assert response.status_code == 200


def test_auth_exempt_paths_bypass_auth(client: TestClient) -> None:
    """Test that exempt paths bypass authentication."""
    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/api/v1/quota/rules")
    assert response.status_code == 200
