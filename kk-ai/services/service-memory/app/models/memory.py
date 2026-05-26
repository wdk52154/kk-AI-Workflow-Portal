"""Pydantic models for conversation memory."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class StoreMemoryRequest(BaseModel):
    """Request to store a conversation memory."""

    session_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    role: str = Field(default="user", pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class StoreMemoryResponse(BaseModel):
    """Response after storing a memory."""

    memory_id: str
    status: str = "stored"


class RecallMemoryRequest(BaseModel):
    """Request to recall conversation memories."""

    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RecallMemoryResult(BaseModel):
    """A single recalled memory."""

    memory_id: str
    role: str
    content: str
    score: float
    timestamp: str


class RecallMemoryResponse(BaseModel):
    """Response from memory recall."""

    query: str
    session_id: str
    results: list[RecallMemoryResult]
    total: int
