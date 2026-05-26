"""Data Service configuration with Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Data Service settings loaded from environment variables."""

    SERVICE_NAME: str = "service-data"
    VERSION: str = "0.1.0"
    PORT: int = 9005
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Database
    DB_PATH: str = Field(default="./data/data.db", description="SQLite database path")

    # External Services
    RAG_SERVICE_URL: str = Field(
        default="http://localhost:9002",
        description="RAG Service base URL",
    )
    MEMORY_SERVICE_URL: str = Field(
        default="http://localhost:9003",
        description="Memory Service base URL",
    )
    LLM_GATEWAY_URL: str = Field(
        default="http://localhost:9001",
        description="LLM Gateway base URL",
    )

    # Data Processing
    BATCH_SIZE_LIMIT: int = Field(default=1000, description="Max records per batch")
    EXPORT_LIMIT: int = Field(default=10000, description="Max records per export")
    QUALITY_THRESHOLD: int = Field(
        default=70, description="Min quality score for data products and vectorization"
    )

    class Config:
        env_prefix = "DATA_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
