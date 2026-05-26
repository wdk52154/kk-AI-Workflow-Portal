"""Pydantic models for data products (sales scripts, objections, user profiles)."""

from typing import Any

from pydantic import BaseModel, Field


class SalesScriptItem(BaseModel):
    """Single sales script item."""

    script_id: str
    content: str
    conversion_rate: float = Field(..., ge=0.0, le=1.0)
    usage_count: int = Field(..., ge=0)
    tags: list[str]
    source_project_id: str
    created_at: str


class SalesScriptsResponse(BaseModel):
    """Response model for sales scripts."""

    scripts: list[SalesScriptItem]
    total: int


class ObjectionItem(BaseModel):
    """Single objection-response pair."""

    objection_id: str
    objection_text: str
    response_text: str
    objection_type: str
    frequency: int = Field(..., ge=0)
    tags: list[str]
    source_project_id: str
    created_at: str


class ObjectionsResponse(BaseModel):
    """Response model for objections."""

    objections: list[ObjectionItem]
    total: int


class UserProfileItem(BaseModel):
    """Single user profile item."""

    user_id: str
    basic: dict[str, Any]
    preferences: list[str]
    constraints: list[str]
    value_score: int = Field(..., ge=0, le=100)
    interaction_count: int = Field(..., ge=0)
    last_interaction: str | None = None
    updated_at: str


class UserProfilesResponse(BaseModel):
    """Response model for user profiles."""

    profiles: list[UserProfileItem]
    total: int
