"""Gateway configuration with Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """LLM Gateway settings loaded from environment variables."""

    SERVICE_NAME: str = "service-llm"
    VERSION: str = "0.1.0"
    PORT: int = 9001
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Doubao ARK
    ARK_API_KEY: str = Field(default="", description="Doubao ARK API Key")
    ARK_BASE_URL: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        description="Doubao ARK API base URL",
    )

    # Model Config
    MODELS_CONFIG_PATH: str = Field(
        default="config/models.yaml",
        description="Path to models YAML config",
    )
    CONFIG_RELOAD_INTERVAL: int = Field(
        default=5,
        description="Config reload check interval in seconds",
    )

    # Circuit Breaker
    CIRCUIT_FAILURE_THRESHOLD: int = 5
    CIRCUIT_RECOVERY_TIMEOUT: float = 30.0

    # Retry
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 1.0

    class Config:
        env_prefix = "LLM_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
