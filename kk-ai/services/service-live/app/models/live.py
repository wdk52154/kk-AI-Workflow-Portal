from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RecordStartRequest(BaseModel):
    stream_url: str = Field(..., min_length=1)
    title: str = Field(default="直播录制")
    platform: str = Field(default="douyin")

class RecordStartResponse(BaseModel):
    record_id: str
    stream_url: str
    status: str
    started_at: str

class RecordStopRequest(BaseModel):
    record_id: str

class RecordStopResponse(BaseModel):
    record_id: str
    status: str
    duration_seconds: int
    video_url: str

class Highlight(BaseModel):
    start_time: float
    end_time: float
    highlight_type: str
    score: float
    description: str

class AnalyzeRequest(BaseModel):
    record_id: str

class AnalyzeResponse(BaseModel):
    record_id: str
    highlights: List[Highlight]
    total_duration: float
    transcript: List[dict]

class ClipRequest(BaseModel):
    record_id: str
    start_time: float
    end_time: float
    title: str = ""

class ClipResponse(BaseModel):
    clip_id: str
    record_id: str
    video_url: str
    duration: float
    title: str

class EnhanceRequest(BaseModel):
    clip_id: str
    add_subtitle: bool = True
    add_bgm: bool = False
    add_intro: bool = True

class EnhanceResponse(BaseModel):
    clip_id: str
    video_url: str
    enhancements: List[str]
    status: str
