"""Tests for quota management API."""

import pytest
from fastapi.testclient import TestClient


def test_create_quota_rule_success(client: TestClient):
    """Test creating a quota rule."""
    response = client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "test-project",
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "alert_threshold": 80,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_name"] == "test-project"
    assert data["daily_limit"] == 1000
    assert data["status"] == "active"


def test_create_duplicate_rule_returns_409(client: TestClient):
    """Test duplicate rule returns 409."""
    # Create first
    client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "dup-project",
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "alert_threshold": 80,
        },
    )
    # Try duplicate
    response = client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "dup-project",
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "alert_threshold": 80,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "RULE_EXISTS"


def test_validation_monthly_less_than_daily(client: TestClient):
    """Test validation when monthly < daily."""
    response = client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "bad-project",
            "daily_limit": 1000,
            "monthly_limit": 500,
            "alert_threshold": 80,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "VALIDATION_ERROR"


def test_get_rule_not_found(client: TestClient):
    """Test getting non-existent rule."""
    response = client.get("/api/v1/quota/rules/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "RULE_NOT_FOUND"


def test_update_rule(client: TestClient):
    """Test updating a rule."""
    # Create
    create_resp = client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "update-project",
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "alert_threshold": 80,
        },
    )
    rule_id = create_resp.json()["id"]

    # Update
    response = client.put(
        f"/api/v1/quota/rules/{rule_id}",
        json={"daily_limit": 2000},
    )
    assert response.status_code == 200
    assert response.json()["daily_limit"] == 2000


def test_delete_rule_soft_delete(client: TestClient):
    """Test soft delete."""
    # Create
    create_resp = client.post(
        "/api/v1/quota/rules",
        json={
            "project_name": "delete-project",
            "daily_limit": 1000,
            "monthly_limit": 30000,
            "alert_threshold": 80,
        },
    )
    rule_id = create_resp.json()["id"]

    # Delete
    response = client.delete(f"/api/v1/quota/rules/{rule_id}")
    assert response.status_code == 204

    # Should not be found in active list
    list_resp = client.get("/api/v1/quota/rules")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert not any(r["id"] == rule_id for r in items)


def test_list_rules_pagination(client: TestClient):
    """Test listing rules with pagination."""
    response = client.get("/api/v1/quota/rules?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_usage_no_rule(client: TestClient):
    """Test usage for project without rule."""
    response = client.get("/api/v1/quota/usage/no-rule-project")
    assert response.status_code == 200
    data = response.json()
    assert data["daily_limit"] == 0
    assert data["monthly_limit"] == 0
    assert data["status"] == "normal"


def test_list_projects(client: TestClient):
    """Test listing projects."""
    response = client.get("/api/v1/quota/projects")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


def test_quota_api_exempt_from_middleware(client: TestClient):
    """Test that quota API paths are accessible without auth."""
    response = client.get("/api/v1/quota/rules")
    assert response.status_code == 200
