"""Tests for prompt management API."""

from fastapi.testclient import TestClient


def test_list_prompts_empty(client: TestClient) -> None:
    """Test listing prompts when empty."""
    response = client.get("/v1/prompts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_register_and_get_prompt(client: TestClient) -> None:
    """Test registering and retrieving a prompt."""
    # Register
    response = client.post(
        "/v1/prompts",
        json={
            "id": "test_greeting",
            "name": "测试问候语",
            "category": "user",
            "description": "简单的问候语模板",
            "variables": [
                {"name": "name", "required": True, "description": "用户名字"}
            ],
            "template": "你好，{{ name }}！欢迎光临。",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["prompt_id"] == "test_greeting"
    assert data["status"] == "registered"

    # Get
    response = client.get("/v1/prompts/test_greeting")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_greeting"
    assert data["name"] == "测试问候语"


def test_get_prompt_not_found(client: TestClient) -> None:
    """Test getting a non-existent prompt."""
    response = client.get("/v1/prompts/non_existent")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "PROMPT_NOT_FOUND"


def test_delete_prompt(client: TestClient) -> None:
    """Test deleting a prompt."""
    # Register first
    client.post(
        "/v1/prompts",
        json={
            "id": "to_delete",
            "name": "待删除",
            "category": "test",
            "template": "test",
        },
    )

    # Delete
    response = client.delete("/v1/prompts/to_delete")
    assert response.status_code == 204

    # Verify gone
    response = client.get("/v1/prompts/to_delete")
    assert response.status_code == 404


def test_list_prompts_with_category_filter(client: TestClient) -> None:
    """Test listing prompts filtered by category."""
    client.post(
        "/v1/prompts",
        json={
            "id": "cat_a",
            "name": "Category A",
            "category": "sales",
            "template": "test",
        },
    )
    client.post(
        "/v1/prompts",
        json={
            "id": "cat_b",
            "name": "Category B",
            "category": "rag",
            "template": "test",
        },
    )

    response = client.get("/v1/prompts?category=sales")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["prompt_id"] == "cat_a"
