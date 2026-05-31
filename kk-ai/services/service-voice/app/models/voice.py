from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    platform: str = Field(default="web")

class ChatResponse(BaseModel):
    session_id: str
    text_reply: str
    audio_url: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    intent: str = "unknown"
    sources: List[str] = Field(default_factory=list)

class AudioChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None

class AudioChatResponse(BaseModel):
    session_id: str
    text_reply: str
    audio_url: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    intent: str = "unknown"

class SessionHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    messages: List[dict]
    created_at: str
    updated_at: str

class TransferRequest(BaseModel):
    session_id: str
    reason: str = "用户要求转人工"

class TransferResponse(BaseModel):
    session_id: str
    status: str = "transferred"
    context_summary: str
    messages: List[dict]
