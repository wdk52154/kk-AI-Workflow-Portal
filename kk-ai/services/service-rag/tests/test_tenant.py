"""Tests for multi-tenant isolation."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _ingest_for_project(client: TestClient, headers: dict, text: bytes) -> str:
    """Helper to ingest a document for a specific project."""
    mock_embeddings = [[0.1] * 1536] * 3
    with patch("app.services.embedding_client.EmbeddingClient.embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings
        response = client.post(
            "/v1/ingest_document",
            headers=headers,
            files={"file": ("tenant_test.txt", BytesIO(text), "text/plain")},
        )
    assert response.status_code == 200
    return response.json()["document_id"]


def test_project_isolation_documents(client: TestClient, project_headers: dict, other_project_headers: dict) -> None:
    """Test that documents are isolated between projects."""
    doc_id_a = _ingest_for_project(client, project_headers, b"Project A content. " * 20)
    doc_id_b = _ingest_for_project(client, other_project_headers, b"Project B content. " * 20)

    # Project A should only see its own documents
    response = client.get("/v1/documents", headers=project_headers)
    data = response.json()
    doc_ids = [d["document_id"] for d in data["documents"]]
    assert doc_id_a in doc_ids
    assert doc_id_b not in doc_ids

    # Project B should only see its own documents
    response = client.get("/v1/documents", headers=other_project_headers)
    data = response.json()
    doc_ids = [d["document_id"] for d in data["documents"]]
    assert doc_id_b in doc_ids
    assert doc_id_a not in doc_ids


def test_project_isolation_search(client: TestClient, project_headers: dict, other_project_headers: dict) -> None:
    """Test that search results are isolated between projects."""
    _ingest_for_project(client, project_headers, b"Project A secret. " * 20)
    _ingest_for_project(client, other_project_headers, b"Project B secret. " * 20)

    query_embedding = [0.1] * 1536
    with patch("app.services.embedding_client.EmbeddingClient.embed_single", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = query_embedding

        response = client.post(
            "/v1/search_knowledge",
            headers=project_headers,
            json={"query": "secret", "top_k": 5},
        )

    assert response.status_code == 200
    data = response.json()
    # Should find Project A content but not Project B
    for result in data["results"]:
        assert "Project A" in result["content"]
        assert "Project B" not in result["content"]


def test_delete_isolation(client: TestClient, project_headers: dict, other_project_headers: dict) -> None:
    """Test that deleting in one project doesn't affect another."""
    doc_id_a = _ingest_for_project(client, project_headers, b"Project A content. " * 20)
    doc_id_b = _ingest_for_project(client, other_project_headers, b"Project B content. " * 20)

    # Delete from Project A
    response = client.delete(f"/v1/documents/{doc_id_a}", headers=project_headers)
    assert response.status_code == 204

    # Project B document should still exist
    response = client.get("/v1/documents", headers=other_project_headers)
    data = response.json()
    doc_ids = [d["document_id"] for d in data["documents"]]
    assert doc_id_b in doc_ids
