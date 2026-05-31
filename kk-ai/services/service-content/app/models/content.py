from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class TopicGenerateRequest(BaseModel):
    industry: str = Field(..., min_length=1)
    account_positioning: str = Field(default="")
    count: int = Field(default=5, ge=1, le=20)

class TopicItem(BaseModel):
    title: str
    category: str
    trending_score: float
    suggested_tags: List[str]
    reason: str

class TopicGenerateResponse(BaseModel):
    topics: List[TopicItem]

class ContentGenerateRequest(BaseModel):
    platform: Literal["xiaohongshu", "wechat", "douyin", "moments"] = "xiaohongshu"
    topic: str = Field(..., min_length=1)
    tone: Literal["lively", "professional", "premium"] = "lively"
    brand: str = Field(default="")
    keywords: List[str] = Field(default_factory=list)
    length: Literal["short", "medium", "long"] = "medium"

class ContentGenerateResponse(BaseModel):
    id: str
    platform: str
    title: str
    content: str
    tags: List[str]
    suggested_images: List[str] = Field(default_factory=list)
    created_at: str

class RewriteRequest(BaseModel):
    content_id: str
    style: Literal["polish", "expand", "shorten", "change_tone"] = "polish"
    tone: Optional[str] = None

class ScheduleRequest(BaseModel):
    content_id: str
    platform: str
    scheduled_at: str
    status: Literal["draft", "scheduled", "published"] = "scheduled"

class ScheduleItem(BaseModel):
    id: str
    content_id: str
    platform: str
    scheduled_at: str
    status: str
    created_at: str
