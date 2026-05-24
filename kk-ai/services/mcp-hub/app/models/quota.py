"""Quota management models."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class QuotaRule(BaseModel):
    """Quota rule for a project."""

    id: str
    project_name: str = Field(min_length=1, max_length=64)
    daily_limit: int = Field(gt=0)
    monthly_limit: int = Field(gt=0)
    alert_threshold: int = Field(ge=1, le=100)
    status: Literal["active", "deleted"] = "active"
    created_at: datetime
    updated_at: datetime


class QuotaRuleCreate(BaseModel):
    """Request model for creating a quota rule."""

    project_name: str = Field(min_length=1, max_length=64)
    daily_limit: int = Field(gt=0)
    monthly_limit: int = Field(gt=0)
    alert_threshold: int = Field(ge=1, le=100)


class QuotaRuleUpdate(BaseModel):
    """Request model for updating a quota rule."""

    daily_limit: int | None = Field(default=None, gt=0)
    monthly_limit: int | None = Field(default=None, gt=0)
    alert_threshold: int | None = Field(default=None, ge=1, le=100)
    status: Literal["active", "deleted"] | None = None


class QuotaUsage(BaseModel):
    """Real-time quota usage for a project."""

    project_name: str
    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int
    usage_rate: float
    status: Literal["normal", "warning", "exceeded"]


class QuotaRuleListResponse(BaseModel):
    """Paginated list of quota rules."""

    items: list[QuotaRule]
    total: int
    page: int
    page_size: int


class ProjectListResponse(BaseModel):
    """List of project names."""

    items: list[str]


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    detail: dict | None = None
