"""Gateway configuration with Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Gateway settings loaded from environment variables."""

    # Service
    SERVICE_NAME: str = "mcp-hub"
    VERSION: str = "0.1.0"
    PORT: int = 8000
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")

    # Auth
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS_JSON: Optional[str] = Field(
        default=None,
        description="JSON string of API keys config (fallback if no Redis)",
    )

    # Rate Limit
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60

    # Quota
    QUOTA_DAILY_DEFAULT: int = 10000
    QUOTA_MONTHLY_DEFAULT: int = 300000

    # Logger
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="json or text")

    # Router
    ROUTES_JSON: Optional[str] = Field(
        default=None,
        description='JSON string of routes config, e.g. [{"service_name":"mcp-a","target_url":"http://localhost:9001"}]',
    )
    REQUEST_TIMEOUT_SECONDS: float = 30.0

    class Config:
        env_prefix = "MCPHUB_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
