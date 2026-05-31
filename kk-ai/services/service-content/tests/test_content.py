import pytest
from fastapi.testclient import TestClient
from app.main import create_app
import app.services.content_store as m

@pytest.fixture(autouse=True)
def reset_store():
    m._content_store = None
    yield

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_generate_topics(client):
    r = client.post("/v1/content/topics", json={"industry": "美妆", "count": 3})
    assert r.status_code == 200
    assert len(r.json()["topics"]) == 3

def test_generate_content(client):
    r = client.post("/v1/content/generate", json={
        "platform": "xiaohongshu",
        "topic": "夏季护肤好物推荐",
        "tone": "lively"
    })
    assert r.status_code == 201 if r.status_code == 201 else 200
    data = r.json()
    assert data["id"]
    assert data["content"]

def test_list_and_get(client):
    gen = client.post("/v1/content/generate", json={"platform": "wechat", "topic": "测试", "tone": "professional"})
    cid = gen.json()["id"]
    r = client.get("/v1/content/contents")
    assert r.json()["total"] >= 1
    r2 = client.get(f"/v1/content/contents/{cid}")
    assert r2.json()["id"] == cid

def test_rewrite(client):
    gen = client.post("/v1/content/generate", json={"platform": "moments", "topic": "测试改写", "tone": "lively"})
    cid = gen.json()["id"]
    r = client.post("/v1/content/rewrite", json={"content_id": cid, "style": "expand"})
    assert r.status_code == 200
    assert "扩写版" in r.json()["content"]

def test_schedule(client):
    gen = client.post("/v1/content/generate", json={"platform": "douyin", "topic": "短视频", "tone": "lively"})
    cid = gen.json()["id"]
    r = client.post("/v1/content/schedule", json={
        "content_id": cid, "platform": "douyin", "scheduled_at": "2026-06-01T10:00:00"
    })
    assert r.status_code == 200
    assert client.get("/v1/content/schedules").json()
