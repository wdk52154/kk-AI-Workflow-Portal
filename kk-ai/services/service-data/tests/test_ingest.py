"""Tests for data ingestion and ETL pipeline."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_rag_client():
    """Helper to mock RAG client ingest_document."""
    return patch(
        "app.services.rag_client.RAGClient.ingest_document",
        new_callable=AsyncMock,
        return_value={"doc_id": "test_doc", "status": "ingested"},
    )


def test_ingest_wechat_data(client: TestClient) -> None:
    """Test ingesting WeChat consultation records."""
    with _mock_rag_client():
        response = client.post(
            "/v1/data/ingest",
            json={
                "source_type": "wechat",
                "project_id": "proj_001",
                "records": [
                    {
                        "raw_id": "wx_msg_001",
                        "content": "你好，我想咨询一下你们的产品价格。",
                        "metadata": {"user_id": "u001", "channel": "wechat"},
                    },
                    {
                        "raw_id": "wx_msg_002",
                        "content": "请问有优惠活动吗？",
                        "metadata": {"user_id": "u002", "channel": "wechat"},
                    },
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["record_count"] == 2
    assert data["success_count"] == 2
    assert data["failed_count"] == 0
    assert data["batch_id"].startswith("batch_")
    assert data["status"] in ("completed", "etl_failed")


def test_ingest_with_desensitization(client: TestClient) -> None:
    """Test that sensitive information is desensitized during ETL."""
    with _mock_rag_client():
        response = client.post(
            "/v1/data/ingest",
            json={
                "source_type": "customer_service",
                "project_id": "proj_002",
                "records": [
                    {
                        "raw_id": "cs_001",
                        "content": "我的手机号是13800138000，身份证号是110101199001011234，邮箱是test@example.com",
                        "metadata": {"user_id": "u003"},
                    },
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["record_count"] == 1

    # Query cleaned data to verify desensitization
    query_resp = client.post(
        "/v1/data/query",
        json={"project_id": "proj_002", "page": 1, "page_size": 10},
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total"] == 1

    cleaned = query_data["items"][0]["cleaned_content"]
    assert "[PHONE]" in cleaned
    assert "[ID]" in cleaned
    assert "[EMAIL]" in cleaned
    assert "13800138000" not in cleaned
    assert "110101199001011234" not in cleaned
    assert "test@example.com" not in cleaned


def test_ingest_batch_too_large(client: TestClient) -> None:
    """Test that batch exceeding limit returns 413."""
    records = [
        {"raw_id": f"rec_{i}", "content": f"content {i}"}
        for i in range(1001)
    ]
    response = client.post(
        "/v1/data/ingest",
        json={
            "source_type": "wechat",
            "project_id": "proj_003",
            "records": records,
        },
    )

    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["error"] == "BATCH_TOO_LARGE"


def test_ingest_deduplication(client: TestClient) -> None:
    """Test that duplicate content is detected and deduplicated."""
    with _mock_rag_client():
        # First batch
        response1 = client.post(
            "/v1/data/ingest",
            json={
                "source_type": "sales_call",
                "project_id": "proj_004",
                "records": [
                    {"raw_id": "sc_001", "content": "完全相同的销售话术内容"},
                ],
            },
        )
        assert response1.status_code == 200

        # Second batch with same content
        response2 = client.post(
            "/v1/data/ingest",
            json={
                "source_type": "sales_call",
                "project_id": "proj_004",
                "records": [
                    {"raw_id": "sc_002", "content": "完全相同的销售话术内容"},
                ],
            },
        )
        assert response2.status_code == 200

    # Query should only have 1 cleaned record due to dedup
    query_resp = client.post(
        "/v1/data/query",
        json={"project_id": "proj_004", "page": 1, "page_size": 10},
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    # One record deduplicated, so only 1 cleaned record remains
    assert query_data["total"] == 1


def test_ingest_invalid_source_type(client: TestClient) -> None:
    """Test ingestion with invalid source type returns 422."""
    response = client.post(
        "/v1/data/ingest",
        json={
            "source_type": "invalid_source",
            "project_id": "proj_005",
            "records": [{"raw_id": "r1", "content": "test"}],
        },
    )
    assert response.status_code == 422
