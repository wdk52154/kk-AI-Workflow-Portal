"""Tests for admin API routes."""

from fastapi.testclient import TestClient


def test_admin_health_no_auth(client: TestClient) -> None:
    """Test that admin health can be accessed without admin key (for monitoring)."""
    response = client.get("/api/v1/admin/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mcp-hub"
    assert "redis_connected" in data


def test_admin_routes_list_requires_admin_key(client: TestClient) -> None:
    """Test that listing routes requires admin key."""
    response = client.get("/api/v1/admin/routes")
    assert response.status_code == 401


def test_admin_routes_list_with_valid_key(client: TestClient) -> None:
    """Test listing routes with valid admin key."""
    response = client.get(
        "/api/v1/admin/routes",
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_admin_create_route_with_valid_key(client: TestClient) -> None:
    """Test creating a route with valid admin key."""
    response = client.post(
        "/api/v1/admin/routes",
        json={
            "service_name": "test-svc",
            "target_url": "http://localhost:9999",
            "description": "Test service",
            "timeout_seconds": 10.0,
        },
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["service_name"] == "test-svc"
    assert data["target_url"] == "http://localhost:9999"


def test_admin_delete_route_with_valid_key(client: TestClient) -> None:
    """Test deleting a route with valid admin key."""
    # First create a route
    create_resp = client.post(
        "/api/v1/admin/routes",
        json={
            "service_name": "delete-test",
            "target_url": "http://localhost:9998",
        },
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    route_id = create_resp.json()["id"]

    # Delete it
    response = client.delete(
        f"/api/v1/admin/routes/{route_id}",
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    assert response.status_code == 204


def test_admin_delete_nonexistent_route_returns_404(client: TestClient) -> None:
    """Test deleting a non-existent route returns 404."""
    response = client.delete(
        "/api/v1/admin/routes/non-existent-id",
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    assert response.status_code == 404


def test_admin_api_keys_list_with_valid_key(client: TestClient) -> None:
    """Test listing API keys with valid admin key."""
    response = client.get(
        "/api/v1/admin/api-keys",
        headers={"X-Admin-Key": "kk-admin-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
