"""Tests for asset API."""

from fastapi.testclient import TestClient


def test_upload_asset(client: TestClient) -> None:
    """Test uploading an asset."""
    response = client.post(
        "/v1/assets",
        data={
            "name": "测试图片",
            "asset_type": "image",
            "description": "一张测试图片",
            "tags": "测试,图片",
            "category": "营销",
        },
        files={"file": ("test.png", b"fake-image-data", "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试图片"
    assert data["asset_type"] == "image"
    assert data["status"] == "uploaded"


def test_search_assets(client: TestClient) -> None:
    """Test searching assets."""
    # Upload first
    client.post(
        "/v1/assets",
        data={"name": "销售海报", "asset_type": "image"},
        files={"file": ("poster.png", b"data", "image/png")},
    )

    response = client.get("/v1/assets/search?q=销售")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_get_asset(client: TestClient) -> None:
    """Test getting asset by ID."""
    upload_resp = client.post(
        "/v1/assets",
        data={"name": "详情测试", "asset_type": "image"},
        files={"file": ("t.png", b"d", "image/png")},
    )
    asset_id = upload_resp.json()["asset_id"]

    response = client.get(f"/v1/assets/{asset_id}")
    assert response.status_code == 200
    assert response.json()["asset_id"] == asset_id


def test_update_status(client: TestClient) -> None:
    """Test updating asset status."""
    upload_resp = client.post(
        "/v1/assets",
        data={"name": "状态测试", "asset_type": "image"},
        files={"file": ("t.png", b"d", "image/png")},
    )
    asset_id = upload_resp.json()["asset_id"]

    response = client.post(
        f"/v1/assets/{asset_id}/status",
        data={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_asset_stats(client: TestClient) -> None:
    """Test asset statistics."""
    # Upload some assets
    for i in range(3):
        client.post(
            "/v1/assets",
            data={"name": f"统计{i}", "asset_type": "image"},
            files={"file": (f"{i}.png", b"d", "image/png")},
        )

    response = client.get("/v1/assets/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_assets"] >= 3


def test_health(client: TestClient) -> None:
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
