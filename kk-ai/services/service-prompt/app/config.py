"""Prompt Center configuration with Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Prompt Center settings loaded from environment variables."""

    SERVICE_NAME: str = "service-prompt"
    VERSION: str = "0.1.0"
    PORT: int = 9004
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    PROMPTS_DIR: str = Field(default="./prompts", description="Prompts YAML directory")
    CONFIG_RELOAD_INTERVAL: int = Field(default=5, description="Config reload interval in seconds")

    class Config:
        env_prefix = "PROMPT_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
