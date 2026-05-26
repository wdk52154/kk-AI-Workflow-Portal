"""Tests for data dashboard statistics."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_rag_client():
    return patch(
        "app.services.rag_client.RAGClient.ingest_document",
        new_callable=AsyncMock,
        return_value={"doc_id": "test_doc", "status": "ingested"},
    )


def test_data_stats_empty(client: TestClient) -> None:
    """Test stats endpoint with empty database."""
    response = client.get("/v1/data/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 0
    assert data["total_cleaned"] == 0
    assert data["total_annotated"] == 0
    assert data["avg_quality_score"] == 0.0
    assert data["records_by_source"] == []
    assert data["records_by_project"] == []
    assert data["annotation_progress"]["annotated"] == 0
    assert data["annotation_progress"]["pending"] == 0


def test_data_stats_with_data(client: TestClient) -> None:
    """Test stats endpoint with data ingested and annotated."""
    with _mock_rag_client():
        client.post(
            "/v1/data/ingest",
            json={
                "source_type": "wechat",
                "project_id": "proj_stats",
                "records": [
                    {"raw_id": "st1", "content": "第一条咨询记录，内容比较长一些。"},
                    {"raw_id": "st2", "content": "第二条投诉记录，服务态度需要改进。"},
                    {"raw_id": "st3", "content": "第三条购买意向记录，希望尽快下单。"},
                ],
            },
        )

    # Annotate all records
    client.post("/v1/data/1/annotate", json={"intent": "咨询", "emotion": "neutral"})
    client.post("/v1/data/2/annotate", json={"intent": "投诉", "emotion": "negative"})
    client.post("/v1/data/3/annotate", json={"intent": "购买意向", "emotion": "positive"})

    response = client.get("/v1/data/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_records"] == 3
    assert data["total_cleaned"] == 3
    assert data["total_annotated"] == 3
    assert data["avg_quality_score"] > 0

    # Check records by source
    source_types = {r["source_type"] for r in data["records_by_source"]}
    assert "wechat" in source_types

    # Check records by project
    project_ids = {r["project_id"] for r in data["records_by_project"]}
    assert "proj_stats" in project_ids

    # Check top intents
    intents = {i["intent"] for i in data["top_intents"]}
    assert "咨询" in intents
    assert "投诉" in intents
    assert "购买意向" in intents

    # Check emotion distribution
    assert "neutral" in data["emotion_distribution"]
    assert "negative" in data["emotion_distribution"]
    assert "positive" in data["emotion_distribution"]

    # Check annotation progress
    assert data["annotation_progress"]["annotated"] == 3
    assert data["annotation_progress"]["total"] == 3


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "service-data"
    assert "version" in data
