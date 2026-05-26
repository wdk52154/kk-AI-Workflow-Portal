"""RAG Service configuration with Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """RAG Service settings loaded from environment variables."""

    SERVICE_NAME: str = "service-rag"
    VERSION: str = "0.1.0"
    PORT: int = 9002
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # LLM Gateway
    LLM_GATEWAY_URL: str = Field(
        default="http://localhost:9001",
        description="LLM Gateway base URL",
    )

    # Vector Store
    VECTOR_STORE_TYPE: str = Field(
        default="memory",
        description="Vector store backend: memory or chromadb",
    )
    VECTOR_STORE_PERSIST_DIR: str = Field(
        default="./chroma_data",
        description="Vector store persistence directory",
    )

    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # Search
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 50

    # Document Upload
    MAX_FILE_SIZE_MB: int = 10
    MAX_CHUNKS_PER_DOC: int = 1000

    class Config:
        env_prefix = "RAG_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
