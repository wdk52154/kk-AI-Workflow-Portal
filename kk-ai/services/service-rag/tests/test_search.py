"""Tests for knowledge search API."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _ingest_test_doc(client: TestClient, headers: dict, text: bytes = b"Hello world. " * 50) -> str:
    """Helper to ingest a test document."""
    mock_embeddings = [[0.1] * 1536] * 5
    with patch("app.services.embedding_client.EmbeddingClient.embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings
        response = client.post(
            "/v1/ingest_document",
            headers=headers,
            data={"source_type": "txt", "tags": "test"},
            files={"file": ("search_test.txt", BytesIO(text), "text/plain")},
        )
    assert response.status_code == 200
    return response.json()["document_id"]


def test_search_basic(client: TestClient, project_headers: dict) -> None:
    """Test basic vector search."""
    _ingest_test_doc(client, project_headers)

    query_embedding = [0.1] * 1536
    with patch("app.services.embedding_client.EmbeddingClient.embed_single", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = query_embedding

        response = client.post(
            "/v1/search_knowledge",
            headers=project_headers,
            json={"query": "hello world", "top_k": 3},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "hello world"
    assert "results" in data
    assert data["total"] > 0


def test_search_with_metadata_filter(client: TestClient, project_headers: dict) -> None:
    """Test search with metadata filters."""
    _ingest_test_doc(client, project_headers)

    query_embedding = [0.1] * 1536
    with patch("app.services.embedding_client.EmbeddingClient.embed_single", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = query_embedding

        response = client.post(
            "/v1/search_knowledge",
            headers=project_headers,
            json={
                "query": "test",
                "top_k": 5,
                "filters": {"source_type": "txt"},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0


def test_search_missing_project_id(client: TestClient) -> None:
    """Test search without X-Project-Id returns 400."""
    response = client.post(
        "/v1/search_knowledge",
        json={"query": "hello", "top_k": 3},
    )
    assert response.status_code == 400


def test_search_rerank(client: TestClient, project_headers: dict) -> None:
    """Test search with rerank enabled."""
    _ingest_test_doc(client, project_headers)

    query_embedding = [0.1] * 1536
    with patch("app.services.embedding_client.EmbeddingClient.embed_single", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = query_embedding

        with patch("app.services.reranker.Reranker.rerank", new_callable=AsyncMock) as mock_rerank:
            mock_rerank.return_value = [
                {"content": "result 1", "score": 0.9, "metadata": {}},
            ]

            response = client.post(
                "/v1/search_knowledge",
                headers=project_headers,
                json={"query": "hello", "top_k": 3, "rerank": True},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["reranked"] is True
