import pytest
from fastapi.testclient import TestClient
from app.main import create_app
import app.services.voice_store as m

@pytest.fixture(autouse=True)
def reset_store():
    m._voice_store = None
    yield

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_chat(client):
    r = client.post("/v1/voice/chat", json={
        "message": "我想买产品",
        "user_id": "user-test-001"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"]
    assert data["text_reply"]
    assert data["intent"]

def test_chat_stream(client):
    r = client.post("/v1/voice/chat/stream", json={
        "message": "介绍一下",
        "user_id": "user-test-002"
    })
    assert r.status_code == 200
    content = r.content.decode()
    assert "data:" in content
    assert "done" in content

def test_session_history(client):
    chat_r = client.post("/v1/voice/chat", json={
        "message": "测试消息",
        "user_id": "user-test-003"
    })
    sid = chat_r.json()["session_id"]

    r = client.get(f"/v1/voice/sessions/{sid}")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert len(data["messages"]) >= 2

def test_transfer(client):
    chat_r = client.post("/v1/voice/chat", json={
        "message": "转人工",
        "user_id": "user-test-004"
    })
    sid = chat_r.json()["session_id"]

    r = client.post("/v1/voice/transfer", json={
        "session_id": sid,
        "reason": "用户要求"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "transferred"
    assert len(data["messages"]) > 0
