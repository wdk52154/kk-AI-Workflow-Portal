from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class ScriptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)
    scenario: str = Field(default="")
    conversion_rate: float = Field(default=0.0, ge=0, le=1)
    objection_target: Optional[str] = Field(default=None)

class ScriptCreate(ScriptBase):
    pass

class ScriptResponse(ScriptBase):
    id: str
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    source: str = "manual"

class SalesQueryRequest(BaseModel):
    customer_question: str = Field(..., min_length=1)
    user_id: Optional[str] = Field(default=None)
    scenario: Optional[str] = Field(default=None)

class SalesQueryResponse(BaseModel):
    recommended_scripts: List[ScriptResponse]
    objection_handler: Optional[str] = None
    user_facts: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)

class RoleplayStartRequest(BaseModel):
    customer_type: Literal["hesitant", "price_sensitive", "clear_need"] = "hesitant"
    scenario: Optional[str] = Field(default=None)
    product: Optional[str] = Field(default=None)

class RoleplayStartResponse(BaseModel):
    session_id: str
    customer_profile: dict
    opening_message: str
    hints: List[str]

class RoleplayChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)

class RoleplayChatResponse(BaseModel):
    customer_reply: str
    real_time_score: dict
    hints: List[str]

class RoleplayEvaluateRequest(BaseModel):
    session_id: str

class RoleplayEvaluateResponse(BaseModel):
    total_score: float
    dimensions: dict
    suggestions: List[str]
    transcript: List[dict]
