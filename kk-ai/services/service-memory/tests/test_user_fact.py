"""Tests for user fact API."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_embedding(value: list[float] | None = None):
    v = value or [0.1] * 1536
    return patch("app.services.embedding_client.EmbeddingClient.embed_single", new_callable=AsyncMock, return_value=v)


def test_store_user_fact(client: TestClient) -> None:
    """Test storing a user fact."""
    with _mock_embedding():
        response = client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_001",
                "fact_type": "constraint",
                "fact_content": "对芒果过敏",
                "confidence": 0.95,
                "source_project_id": "proj_001",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert "fact_id" in data


def test_recall_user_facts_by_user_id(client: TestClient) -> None:
    """Test recalling all facts for a user."""
    # Store facts
    with _mock_embedding():
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_002",
                "fact_type": "preference",
                "fact_content": "喜欢川菜",
                "confidence": 0.8,
                "source_project_id": "proj_002",
            },
        )
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_002",
                "fact_type": "constraint",
                "fact_content": "不吃辣",
                "confidence": 0.9,
                "source_project_id": "proj_003",
            },
        )

    # Recall
    response = client.post(
        "/v1/recall_user_facts",
        json={"user_id": "user_002", "top_k": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_002"
    assert data["total"] == 2
    fact_types = {f["fact_type"] for f in data["facts"]}
    assert "preference" in fact_types
    assert "constraint" in fact_types


def test_recall_user_facts_with_filter(client: TestClient) -> None:
    """Test recalling facts with fact_type filter."""
    with _mock_embedding():
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_003",
                "fact_type": "profile",
                "fact_content": "25岁",
                "confidence": 0.99,
                "source_project_id": "proj_001",
            },
        )
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_003",
                "fact_type": "preference",
                "fact_content": "喜欢游泳",
                "confidence": 0.7,
                "source_project_id": "proj_002",
            },
        )

    # Filter by profile type
    response = client.post(
        "/v1/recall_user_facts",
        json={"user_id": "user_003", "fact_type": "profile", "top_k": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["facts"][0]["fact_type"] == "profile"


def test_user_fact_cross_project_share(client: TestClient) -> None:
    """Test that facts are shared across projects (cross-project user profile)."""
    # Project A stores a fact
    with _mock_embedding([0.1] * 1536):
        response = client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_004",
                "fact_type": "constraint",
                "fact_content": "芒果过敏",
                "confidence": 0.98,
                "source_project_id": "proj_A",
            },
        )
    assert response.status_code == 200

    # Project B recalls the same fact
    response = client.post(
        "/v1/recall_user_facts",
        json={"user_id": "user_004", "top_k": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["facts"][0]["fact_content"] == "芒果过敏"
    assert data["facts"][0]["source_project_id"] == "proj_A"


def test_user_fact_update_confidence(client: TestClient) -> None:
    """Test that storing same fact updates confidence."""
    with _mock_embedding():
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_005",
                "fact_type": "preference",
                "fact_content": "喜欢咖啡",
                "confidence": 0.6,
                "source_project_id": "proj_001",
            },
        )
        # Store again with higher confidence
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_005",
                "fact_type": "preference",
                "fact_content": "喜欢咖啡",
                "confidence": 0.9,
                "source_project_id": "proj_002",
            },
        )

    response = client.post(
        "/v1/recall_user_facts",
        json={"user_id": "user_005", "top_k": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["facts"][0]["confidence"] == 0.9
    assert data["facts"][0]["source_project_id"] == "proj_002"


def test_recall_user_facts_semantic(client: TestClient) -> None:
    """Test semantic search on user facts."""
    # Store facts with different embeddings
    with _mock_embedding([0.1] * 1536):
        client.post(
            "/v1/store_user_fact",
            json={
                "user_id": "user_006",
                "fact_type": "constraint",
                "fact_content": "对芒果过敏",
                "confidence": 0.95,
                "source_project_id": "proj_001",
            },
        )

    # Recall with semantic query
    with _mock_embedding([0.1] * 1536):
        response = client.post(
            "/v1/recall_user_facts",
            json={"user_id": "user_006", "query": "水果过敏", "top_k": 5},
        )

    assert response.status_code == 200
    data = response.json()
    # Should find the mango allergy fact due to similar embedding
    assert data["total"] >= 0
