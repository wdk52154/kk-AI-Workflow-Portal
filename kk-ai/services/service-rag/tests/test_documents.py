"""Tests for document management API."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _ingest_test_doc(client: TestClient, headers: dict) -> str:
    """Helper to ingest a test document."""
    mock_embeddings = [[0.1] * 1536] * 3
    with patch("app.services.embedding_client.EmbeddingClient.embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings
        response = client.post(
            "/v1/ingest_document",
            headers=headers,
            files={"file": ("doc_test.txt", BytesIO(b"Hello world. " * 30), "text/plain")},
        )
    assert response.status_code == 200
    return response.json()["document_id"]


def test_list_documents(client: TestClient, project_headers: dict) -> None:
    """Test listing documents."""
    _ingest_test_doc(client, project_headers)

    response = client.get("/v1/documents", headers=project_headers)
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert data["total"] > 0


def test_delete_document(client: TestClient, project_headers: dict) -> None:
    """Test deleting a document."""
    doc_id = _ingest_test_doc(client, project_headers)

    response = client.delete(f"/v1/documents/{doc_id}", headers=project_headers)
    assert response.status_code == 204

    # Verify document is gone
    response = client.get("/v1/documents", headers=project_headers)
    data = response.json()
    assert not any(d["document_id"] == doc_id for d in data["documents"])


def test_delete_nonexistent_document(client: TestClient, project_headers: dict) -> None:
    """Test deleting a non-existent document returns 404."""
    response = client.delete("/v1/documents/non-existent-id", headers=project_headers)
    assert response.status_code == 404


def test_get_document_chunks(client: TestClient, project_headers: dict) -> None:
    """Test getting document chunks."""
    doc_id = _ingest_test_doc(client, project_headers)

    response = client.get(f"/v1/documents/{doc_id}/chunks", headers=project_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc_id
    assert "chunks" in data
    assert data["total"] > 0


def test_get_chunks_nonexistent_document(client: TestClient, project_headers: dict) -> None:
    """Test getting chunks for non-existent document returns 404."""
    response = client.get("/v1/documents/non-existent-id/chunks", headers=project_headers)
    assert response.status_code == 404
