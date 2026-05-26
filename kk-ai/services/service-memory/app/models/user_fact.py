"""Pydantic models for user facts."""

from typing import Literal

from pydantic import BaseModel, Field


class StoreUserFactRequest(BaseModel):
    """Request to store a user fact."""

    user_id: str = Field(..., min_length=1)
    fact_type: Literal["preference", "constraint", "profile", "behavior"]
    fact_content: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_project_id: str = Field(..., min_length=1)


class StoreUserFactResponse(BaseModel):
    """Response after storing a user fact."""

    fact_id: str
    status: str = "stored"


class RecallUserFactsRequest(BaseModel):
    """Request to recall user facts."""

    user_id: str = Field(..., min_length=1)
    fact_type: str | None = Field(default=None)
    query: str | None = Field(default=None)
    top_k: int = Field(default=10, ge=1, le=50)


class UserFactResult(BaseModel):
    """A single user fact."""

    fact_id: str
    fact_type: str
    fact_content: str
    confidence: float
    source_project_id: str
    score: float | None = None
    created_at: str
    updated_at: str


class RecallUserFactsResponse(BaseModel):
    """Response from user facts recall."""

    user_id: str
    total: int
    facts: list[UserFactResult]
