"""Tests for embedding API."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


def test_embedding_model_not_found(client: TestClient) -> None:
    """Test embedding with non-existent model returns 404."""
    response = client.post(
        "/v1/embeddings",
        json={"model": "non-existent-model", "input": "hello"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "MODEL_NOT_FOUND"


def test_embedding_not_supported(client: TestClient) -> None:
    """Test embedding with non-embedding model returns 400."""
    response = client.post(
        "/v1/embeddings",
        json={"model": "doubao-lite-4k", "input": "hello"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "EMBEDDING_NOT_SUPPORTED"


def test_embedding_success_mock(client: TestClient) -> None:
    """Test successful embedding with mocked ARK response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3],
                "index": 0,
            }
        ],
        "model": "doubao-embedding",
        "usage": {"prompt_tokens": 2, "total_tokens": 2},
    }

    with patch("app.services.ark_client.ArkClient.embeddings", return_value=mock_response):
        with patch("app.services.ark_client.ArkClient.close", new_callable=AsyncMock):
            response = client.post(
                "/v1/embeddings",
                json={"model": "doubao-embedding", "input": "hello"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"][0]["embedding"]) == 3


def test_embedding_batch_input(client: TestClient) -> None:
    """Test embedding with list input."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": [0.1], "index": 0},
            {"object": "embedding", "embedding": [0.2], "index": 1},
        ],
        "model": "doubao-embedding",
        "usage": {"prompt_tokens": 4, "total_tokens": 4},
    }

    with patch("app.services.ark_client.ArkClient.embeddings", return_value=mock_response):
        with patch("app.services.ark_client.ArkClient.close", new_callable=AsyncMock):
            response = client.post(
                "/v1/embeddings",
                json={"model": "doubao-embedding", "input": ["hello", "world"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2
