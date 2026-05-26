"""Tests for document ingestion API."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _create_upload_file(content: bytes, filename: str) -> tuple:
    """Helper to create multipart form data for file upload."""
    return ("file", (filename, BytesIO(content), "text/plain"))


def test_ingest_txt_success(client: TestClient, project_headers: dict) -> None:
    """Test ingesting a txt file."""
    mock_embeddings = [[0.1] * 1536] * 10  # Mock 10 chunks

    with patch("app.services.embedding_client.EmbeddingClient.embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings

        response = client.post(
            "/v1/ingest_document",
            headers=project_headers,
            data={"source_type": "txt", "tags": "test,doc"},
            files={"file": ("test.txt", BytesIO(b"Hello world. " * 100), "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunk_count"] > 0
    assert "document_id" in data


def test_ingest_md_success(client: TestClient, project_headers: dict) -> None:
    """Test ingesting a markdown file with header splitting."""
    mock_embeddings = [[0.2] * 1536] * 5

    with patch("app.services.embedding_client.EmbeddingClient.embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings

        md_content = b"# Title\n\nIntro text.\n\n## Section 1\n\nContent one.\n\n## Section 2\n\nContent two."
        response = client.post(
            "/v1/ingest_document",
            headers=project_headers,
            files={"file": ("test.md", BytesIO(md_content), "text/markdown")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_ingest_missing_project_id(client: TestClient) -> None:
    """Test ingestion without X-Project-Id returns 400."""
    response = client.post(
        "/v1/ingest_document",
        files={"file": ("test.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "MISSING_PROJECT_ID"


def test_ingest_unsupported_format(client: TestClient, project_headers: dict) -> None:
    """Test ingestion with unsupported file format returns 400."""
    response = client.post(
        "/v1/ingest_document",
        headers=project_headers,
        files={"file": ("test.jpg", BytesIO(b"fake image"), "image/jpeg")},
    )
    assert response.status_code == 400


def test_ingest_empty_file(client: TestClient, project_headers: dict) -> None:
    """Test ingestion with empty file returns 400."""
    response = client.post(
        "/v1/ingest_document",
        headers=project_headers,
        files={"file": ("empty.txt", BytesIO(b""), "text/plain")},
    )
    assert response.status_code == 400
