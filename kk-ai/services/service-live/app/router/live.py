from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.live import (
    RecordStartRequest, RecordStartResponse, RecordStopRequest, RecordStopResponse,
    AnalyzeRequest, AnalyzeResponse, ClipRequest, ClipResponse,
    EnhanceRequest, EnhanceResponse, Highlight
)
from app.services.live_store import get_live_store
from app.services.analyzer import analyze_video, enhance_clip
from app.config import get_settings
import time

router = APIRouter(prefix="/v1/live", tags=["live"])

@router.post("/record/start", response_model=RecordStartResponse)
async def start_record(body: RecordStartRequest):
    store = get_live_store()
    rid = store.start_record(body.stream_url, body.title, body.platform)
    return RecordStartResponse(
        record_id=rid, stream_url=body.stream_url,
        status="recording", started_at=store.get_record(rid)["started_at"]
    )

@router.post("/record/stop", response_model=RecordStopResponse)
async def stop_record(body: RecordStopRequest):
    store = get_live_store()
    record = store.get_record(body.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record["status"] != "recording":
        raise HTTPException(status_code=400, detail="Record is not active")

    # 模拟计算录制时长
    duration = 3600  # 模拟1小时
    video_url = f"/data/videos/{body.record_id}.mp4"
    updated = store.stop_record(body.record_id, duration, video_url)
    return RecordStopResponse(
        record_id=body.record_id, status="stopped",
        duration_seconds=updated["duration_seconds"],
        video_url=updated["video_url"]
    )

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    store = get_live_store()
    record = store.get_record(body.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    highlights, transcript = await analyze_video(
        body.record_id, record.get("duration_seconds", 3600)
    )
    store.save_analysis(body.record_id, highlights, transcript)

    return AnalyzeResponse(
        record_id=body.record_id,
        highlights=[Highlight(**h) for h in highlights],
        total_duration=record.get("duration_seconds", 3600),
        transcript=transcript
    )

@router.post("/clip", response_model=ClipResponse)
async def create_clip(body: ClipRequest):
    store = get_live_store()
    record = store.get_record(body.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    duration = body.end_time - body.start_time
    title = body.title or f"切片-{body.start_time:.0f}s-{body.end_time:.0f}s"
    video_url = f"/data/clips/{body.record_id}_{body.start_time:.0f}_{body.end_time:.0f}.mp4"

    cid = store.create_clip(
        body.record_id, title, body.start_time, body.end_time, duration, video_url
    )
    return ClipResponse(
        clip_id=cid, record_id=body.record_id,
        video_url=video_url, duration=duration, title=title
    )

@router.post("/clip/enhance", response_model=EnhanceResponse)
async def enhance(body: EnhanceRequest):
    store = get_live_store()
    clip = store.get_clip(body.clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    settings = get_settings()
    video_url, enhancements = await enhance_clip(
        body.clip_id, body.add_subtitle, body.add_bgm, body.add_intro,
        settings.ASSET_SERVICE_URL
    )

    store.update_clip(body.clip_id, {
        "enhancements": enhancements,
        "status": "enhanced"
    })

    return EnhanceResponse(
        clip_id=body.clip_id, video_url=video_url,
        enhancements=enhancements, status="enhanced"
    )

@router.get("/clips")
async def list_clips(record_id: Optional[str] = None):
    store = get_live_store()
    return store.list_clips(record_id)

@router.get("/records")
async def list_records():
    store = get_live_store()
    # 简单返回所有记录
    import sqlite3
    conn = sqlite3.connect(store.db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM records ORDER BY started_at DESC')
    rows = c.fetchall()
    conn.close()
    return [{"record_id": r[0], "title": r[2], "platform": r[3],
             "status": r[4], "duration_seconds": r[5],
             "started_at": r[9]} for r in rows]
