"""Pydantic models for document ingestion."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IngestDocumentResponse(BaseModel):
    """Response from document ingestion."""

    document_id: str
    filename: str
    chunk_count: int
    status: str = "success"
    message: str | None = None
