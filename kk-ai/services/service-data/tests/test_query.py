"""Tests for data query and export."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_rag_client():
    """Helper to mock RAG client ingest_document."""
    return patch(
        "app.services.rag_client.RAGClient.ingest_document",
        new_callable=AsyncMock,
        return_value={"doc_id": "test_doc", "status": "ingested"},
    )


def _ingest_test_data(client: TestClient) -> None:
    """Helper to ingest test data."""
    with _mock_rag_client():
        client.post(
            "/v1/data/ingest",
            json={
                "source_type": "wechat",
                "project_id": "proj_query",
                "records": [
                    {"raw_id": "q1", "content": "咨询产品A的功能和价格"},
                    {"raw_id": "q2", "content": "投诉售后服务态度不好"},
                    {"raw_id": "q3", "content": "购买意向强烈，希望尽快发货"},
                ],
            },
        )

    # Annotate some records
    client.post("/v1/data/1/annotate", json={"intent": "咨询", "emotion": "neutral", "tags": ["产品咨询"]})
    client.post("/v1/data/2/annotate", json={"intent": "投诉", "emotion": "negative", "tags": ["售后"]})
    client.post("/v1/data/3/annotate", json={"intent": "购买意向", "emotion": "positive", "tags": ["高意向"]})


def test_query_by_project_id(client: TestClient) -> None:
    """Test querying data by project ID."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/query",
        json={"project_id": "proj_query", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_query_by_intent(client: TestClient) -> None:
    """Test querying data by intent filter."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/query",
        json={"project_id": "proj_query", "intent": "投诉", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["intent"] == "投诉"


def test_query_by_emotion(client: TestClient) -> None:
    """Test querying data by emotion filter."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/query",
        json={"project_id": "proj_query", "emotion": "positive", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["emotion"] == "positive"


def test_query_pagination(client: TestClient) -> None:
    """Test query pagination."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/query",
        json={"project_id": "proj_query", "page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_query_by_min_quality_score(client: TestClient) -> None:
    """Test querying data with minimum quality score filter."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/query",
        json={"project_id": "proj_query", "min_quality_score": 80, "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0


def test_export_json(client: TestClient) -> None:
    """Test exporting data as JSON."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/export",
        json={
            "format": "json",
            "project_id": "proj_query",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["record_count"] == 3
    assert "export_id" in data
    assert len(data["data"]) == 3


def test_export_csv_format_request(client: TestClient) -> None:
    """Test export with CSV format request."""
    _ingest_test_data(client)

    response = client.post(
        "/v1/data/export",
        json={
            "format": "csv",
            "project_id": "proj_query",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert data["record_count"] == 3
