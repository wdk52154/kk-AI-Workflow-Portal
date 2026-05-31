from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class ConversationCreate(BaseModel):
    session_id: str = Field(..., min_length=1)
    conversation_type: Literal["roleplay", "real"] = "roleplay"
    transcript: List[dict] = Field(default_factory=list)
    total_score: Optional[float] = Field(default=None, ge=0, le=100)
    quality_marked: bool = Field(default=False)
    metadata: dict = Field(default_factory=dict)

class ConversationResponse(BaseModel):
    id: str
    session_id: str
    conversation_type: str
    transcript: List[dict]
    total_score: Optional[float]
    quality_marked: bool
    metadata: dict
    created_at: datetime
