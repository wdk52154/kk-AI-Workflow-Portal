import pytest
from fastapi.testclient import TestClient
from app.main import create_app
import app.services.live_store as m

@pytest.fixture(autouse=True)
def reset_store():
    m._live_store = None
    yield

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_record_start_stop(client):
    start = client.post("/v1/live/record/start", json={
        "stream_url": "rtmp://example.com/live/test",
        "title": "测试直播",
        "platform": "douyin"
    })
    assert start.status_code == 200
    rid = start.json()["record_id"]
    assert start.json()["status"] == "recording"

    stop = client.post("/v1/live/record/stop", json={"record_id": rid})
    assert stop.status_code == 200
    assert stop.json()["status"] == "stopped"

def test_analyze(client):
    start = client.post("/v1/live/record/start", json={
        "stream_url": "rtmp://example.com/live/test2",
        "title": "分析测试",
    })
    rid = start.json()["record_id"]
    client.post("/v1/live/record/stop", json={"record_id": rid})

    r = client.post("/v1/live/analyze", json={"record_id": rid})
    assert r.status_code == 200
    data = r.json()
    assert len(data["highlights"]) >= 2
    assert len(data["transcript"]) > 0

def test_clip_and_enhance(client):
    start = client.post("/v1/live/record/start", json={
        "stream_url": "rtmp://example.com/live/test3",
        "title": "切片测试",
    })
    rid = start.json()["record_id"]
    client.post("/v1/live/record/stop", json={"record_id": rid})

    clip = client.post("/v1/live/clip", json={
        "record_id": rid,
        "start_time": 120,
        "end_time": 180,
        "title": "高光片段"
    })
    assert clip.status_code == 200
    cid = clip.json()["clip_id"]

    enhance = client.post("/v1/live/clip/enhance", json={
        "clip_id": cid,
        "add_subtitle": True,
        "add_bgm": True,
        "add_intro": True,
    })
    assert enhance.status_code == 200
    assert enhance.json()["status"] == "enhanced"
    assert len(enhance.json()["enhancements"]) == 3

def test_list_clips(client):
    assert client.get("/v1/live/clips").status_code == 200
    assert client.get("/v1/live/records").status_code == 200
