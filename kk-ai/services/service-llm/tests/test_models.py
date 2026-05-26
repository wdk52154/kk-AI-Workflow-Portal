"""Tests for model list API."""

from fastapi.testclient import TestClient


def test_list_models(client: TestClient) -> None:
    """Test listing available models."""
    response = client.get("/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert len(data["data"]) > 0

    # Check model structure
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert model["object"] == "model"


def test_list_models_includes_chat_models(client: TestClient) -> None:
    """Test that chat-capable models are listed."""
    response = client.get("/v1/models")
    data = response.json()

    model_ids = [m["id"] for m in data["data"]]
    assert "doubao-lite-4k" in model_ids
    assert "doubao-pro-128k" in model_ids


def test_list_models_includes_embedding_models(client: TestClient) -> None:
    """Test that embedding-capable models are listed."""
    response = client.get("/v1/models")
    data = response.json()

    model_ids = [m["id"] for m in data["data"]]
    assert "doubao-embedding" in model_ids
