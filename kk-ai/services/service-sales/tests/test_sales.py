import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.script_store import get_script_store

@pytest.fixture(autouse=True)
def reset_store(tmp_path):
    import app.services.script_store as m
    m._script_store = None
    yield

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_script(client):
    payload = {
        "title": "夏季大促话术",
        "content": "您好，我们现在正在进行夏季大促活动，全场五折起！",
        "category": "promotion",
        "tags": ["促销", "夏季"],
        "scenario": "电话销售",
        "conversion_rate": 0.35
    }
    r = client.post("/v1/sales/scripts", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == payload["title"]
    assert data["id"]
    return data["id"]

def test_list_scripts(client):
    client.post("/v1/sales/scripts", json={
        "title": "话术A",
        "content": "内容A",
        "category": "test"
    })
    r = client.get("/v1/sales/scripts")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert "data" in data

def test_get_script(client):
    sid = test_create_script(client)
    r = client.get(f"/v1/sales/scripts/{sid}")
    assert r.status_code == 200
    assert r.json()["id"] == sid

def test_delete_script(client):
    sid = test_create_script(client)
    r = client.delete(f"/v1/sales/scripts/{sid}")
    assert r.status_code == 204
    r2 = client.get(f"/v1/sales/scripts/{sid}")
    assert r2.status_code == 404

def test_sales_query(client):
    client.post("/v1/sales/scripts", json={
        "title": "过敏提醒话术",
        "content": "如果您对芒果过敏，请避免购买含芒果成分的产品。",
        "category": "health",
        "tags": ["过敏", "健康"]
    })
    r = client.post("/v1/sales/query", json={
        "customer_question": "我对芒果过敏，有什么推荐？",
        "user_id": "user-test-001"
    })
    assert r.status_code == 200
    data = r.json()
    assert "recommended_scripts" in data

def test_roleplay_start(client):
    r = client.post("/v1/sales/roleplay/start", json={
        "customer_type": "hesitant",
        "scenario": "电话销售",
        "product": "护肤品套装"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"]
    assert data["opening_message"]
    assert len(data["hints"]) > 0
    return data["session_id"]

def test_roleplay_chat(client):
    sid = test_roleplay_start(client)
    r = client.post("/v1/sales/roleplay/chat", json={
        "session_id": sid,
        "message": "您好，我们的产品质量很好，您放心购买。"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["customer_reply"]
    assert "real_time_score" in data

def test_roleplay_evaluate(client):
    sid = test_roleplay_start(client)
    client.post("/v1/sales/roleplay/chat", json={
        "session_id": sid,
        "message": "test"
    })
    r = client.post("/v1/sales/roleplay/evaluate", json={
        "session_id": sid
    })
    assert r.status_code == 200
    data = r.json()
    assert data["total_score"] >= 0
    assert len(data["suggestions"]) > 0
