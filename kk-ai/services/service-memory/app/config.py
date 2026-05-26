"""Memory Service configuration with Pydantic Settings."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Memory Service settings loaded from environment variables."""

    SERVICE_NAME: str = "service-memory"
    VERSION: str = "0.1.0"
    PORT: int = 9003
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # LLM Gateway
    LLM_GATEWAY_URL: str = Field(
        default="http://localhost:9001",
        description="LLM Gateway base URL",
    )

    # Database
    DB_PATH: str = Field(default="./data/memory.db", description="SQLite database path")

    # Hot Data
    HOT_DATA_TTL_DAYS: int = Field(default=7, description="Hot data TTL in days")

    class Config:
        env_prefix = "MEMORY_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
