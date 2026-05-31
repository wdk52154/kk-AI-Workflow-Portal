"""Asset Service configuration with Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Asset Service settings loaded from environment variables."""

    SERVICE_NAME: str = "service-asset"
    VERSION: str = "0.1.0"
    PORT: int = 9010
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Database
    DB_PATH: str = Field(default="./data/assets.db", description="SQLite database path")
    STORAGE_PATH: str = Field(default="./data/storage", description="Asset storage directory")

    # External Services
    RAG_SERVICE_URL: str = Field(
        default="http://localhost:9002",
        description="RAG Service base URL",
    )
    PROMPT_SERVICE_URL: str = Field(
        default="http://localhost:9004",
        description="Prompt Center base URL",
    )

    class Config:
        env_prefix = "ASSET_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
