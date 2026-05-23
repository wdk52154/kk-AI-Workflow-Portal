"""Pydantic schemas for mcp-hub gateway."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project configuration with API key and quotas."""

    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project display name")
    api_key: str = Field(..., description="X-API-Key for authentication")
    daily_quota: int = Field(default=10000, description="Daily call limit")
    monthly_quota: int = Field(default=300000, description="Monthly call limit")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    enabled: bool = Field(default=True, description="Whether the project is active")


class RouteConfig(BaseModel):
    """Downstream service route configuration."""

    service_name: str = Field(..., description="Service identifier in URL path")
    target_url: str = Field(..., description="Downstream base URL")
    description: Optional[str] = Field(default=None, description="Service description")
    timeout_seconds: float = Field(default=30.0, description="Request timeout")


class GatewayError(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    trace_id: str = Field(..., description="Request trace ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded", "down"] = "ok"
    service: str = "mcp-hub"
    version: str = "0.1.0"
    redis_connected: bool = False
    upstream_services: dict[str, str] = Field(default_factory=dict)
