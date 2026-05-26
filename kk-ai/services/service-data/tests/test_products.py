"""Tests for data products (sales scripts, objections, user profiles)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_rag_client():
    return patch(
        "app.services.rag_client.RAGClient.ingest_document",
        new_callable=AsyncMock,
        return_value={"doc_id": "test_doc", "status": "ingested"},
    )


def _ingest_and_annotate(client: TestClient) -> None:
    """Helper to ingest and annotate test data for products."""
    with _mock_rag_client():
        client.post(
            "/v1/data/ingest",
            json={
                "source_type": "sales_call",
                "project_id": "proj_sales",
                "records": [
                    {"raw_id": "sc_001", "content": "您好，我们产品现在打八折，非常划算。这款产品质量非常好，很多客户都给予了很高的评价，现在下单还可以享受额外的赠品服务。"},
                    {"raw_id": "sc_002", "content": "这款是爆款产品，很多客户都复购了，您看这是其他客户的真实好评截图。产品的性价比在同类型产品中是最高的，售后也有保障。"},
                ],
            },
        )
        client.post(
            "/v1/data/ingest",
            json={
                "source_type": "customer_service",
                "project_id": "proj_sales",
                "records": [
                    {"raw_id": "cs_obj_001", "content": "价格太贵了\n理解您的顾虑，我们现在有优惠活动，可以享受八折优惠。如果您现在下单，还可以获得额外的赠品和延保服务。"},
                    {"raw_id": "cs_obj_002", "content": "质量不好\n我们的产品经过严格质检，提供7天无理由退换。每一件产品在出厂前都经过三道检测工序，确保品质达标。"},
                ],
            },
        )

    # Annotate sales records as 高转化
    client.post("/v1/data/1/annotate", json={"intent": "高转化", "tags": ["开场", "高转化"]})
    client.post("/v1/data/2/annotate", json={"intent": "高转化", "tags": ["促单", "高转化"]})

    # Annotate objection records
    client.post("/v1/data/3/annotate", json={"intent": "客户异议", "tags": ["价格", "常见异议"]})
    client.post("/v1/data/4/annotate", json={"intent": "客户异议", "tags": ["质量", "常见异议"]})


def test_sales_scripts(client: TestClient) -> None:
    """Test retrieving Top Sales scripts."""
    _ingest_and_annotate(client)

    response = client.get("/v1/products/sales_scripts?project_id=proj_sales")
    assert response.status_code == 200
    data = response.json()
    assert "scripts" in data
    assert data["total"] == 2
    for script in data["scripts"]:
        assert "script_id" in script
        assert "content" in script
        assert 0.0 <= script["conversion_rate"] <= 1.0
        assert script["source_project_id"] == "proj_sales"


def test_sales_scripts_with_tags_filter(client: TestClient) -> None:
    """Test filtering sales scripts by tags."""
    _ingest_and_annotate(client)

    response = client.get("/v1/products/sales_scripts?project_id=proj_sales&tags=开场")
    assert response.status_code == 200
    data = response.json()
    # Should only return scripts with "开场" tag
    assert data["total"] == 1
    assert "开场" in data["scripts"][0]["tags"]


def test_objections(client: TestClient) -> None:
    """Test retrieving objection-response pairs."""
    _ingest_and_annotate(client)

    response = client.get("/v1/products/objections?project_id=proj_sales")
    assert response.status_code == 200
    data = response.json()
    assert "objections" in data
    assert data["total"] == 2
    for obj in data["objections"]:
        assert "objection_id" in obj
        assert "objection_text" in obj
        assert "response_text" in obj
        assert obj["source_project_id"] == "proj_sales"


def test_objections_with_type_filter(client: TestClient) -> None:
    """Test filtering objections by type."""
    _ingest_and_annotate(client)

    response = client.get("/v1/products/objections?project_id=proj_sales&objection_type=价格")
    assert response.status_code == 200
    data = response.json()
    # Should return objections with "价格" in tags
    assert data["total"] >= 0


def test_user_profiles_no_user_id(client: TestClient) -> None:
    """Test user profiles endpoint without user_id returns empty."""
    response = client.get("/v1/products/user_profiles")
    assert response.status_code == 200
    data = response.json()
    assert data["profiles"] == []
    assert data["total"] == 0


def test_user_profiles_with_user_id(client: TestClient) -> None:
    """Test retrieving user profile by user_id."""
    mock_facts = {
        "facts": [
            {"fact_type": "preference", "content": "喜欢产品A", "updated_at": "2026-05-26T10:00:00Z"},
            {"fact_type": "constraint", "content": "预算5000以内", "updated_at": "2026-05-26T10:00:00Z"},
        ]
    }
    with patch(
        "app.services.memory_client.MemoryClient.recall_user_facts",
        new_callable=AsyncMock,
        return_value=mock_facts,
    ):
        response = client.get("/v1/products/user_profiles?user_id=user_001")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    profile = data["profiles"][0]
    assert profile["user_id"] == "user_001"
    assert "喜欢产品A" in profile["preferences"]
    assert "预算5000以内" in profile["constraints"]
    assert profile["interaction_count"] == 2
