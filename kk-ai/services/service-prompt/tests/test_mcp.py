"""Tests for MCP-compatible prompt API."""

from fastapi.testclient import TestClient


def test_mcp_list_prompts(client: TestClient) -> None:
    """Test MCP-compatible prompt list."""
    # Register some prompts
    client.post(
        "/v1/prompts",
        json={
            "id": "mcp_test_1",
            "name": "MCP Test 1",
            "category": "system",
            "description": "First MCP prompt",
            "template": "Hello",
        },
    )
    client.post(
        "/v1/prompts",
        json={
            "id": "mcp_test_2",
            "name": "MCP Test 2",
            "category": "user",
            "description": "Second MCP prompt",
            "template": "World",
        },
    )

    response = client.get("/mcp/prompts")
    assert response.status_code == 200
    data = response.json()
    assert "prompts" in data
    assert len(data["prompts"]) == 2


def test_mcp_get_prompt_detail(client: TestClient) -> None:
    """Test MCP-compatible prompt detail."""
    client.post(
        "/v1/prompts",
        json={
            "id": "mcp_detail",
            "name": "MCP Detail",
            "category": "system",
            "description": "A detailed prompt",
            "variables": [
                {"name": "name", "required": True, "description": "User name"},
                {"name": "age", "required": False, "description": "User age"},
            ],
            "template": "Hello {{ name }}",
        },
    )

    response = client.get("/mcp/prompts/mcp_detail")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mcp_detail"
    assert data["description"] == "A detailed prompt"
    assert len(data["arguments"]) == 2
    assert data["arguments"][0]["name"] == "name"
    assert data["arguments"][0]["required"] is True


def test_mcp_get_prompt_not_found(client: TestClient) -> None:
    """Test MCP getting non-existent prompt returns 404."""
    response = client.get("/mcp/prompts/non_existent")
    assert response.status_code == 404
