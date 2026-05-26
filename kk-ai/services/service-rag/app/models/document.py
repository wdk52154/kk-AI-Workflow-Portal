"""Pydantic models for document management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Information about an ingested document."""

    document_id: str
    filename: str
    source_type: str
    chunk_count: int
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None


class DocumentListResponse(BaseModel):
    """Response for document list."""

    documents: list[DocumentInfo]
    total: int


class ChunkInfo(BaseModel):
    """Information about a single chunk."""

    chunk_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]


class DocumentChunksResponse(BaseModel):
    """Response for document chunks."""

    document_id: str
    chunks: list[ChunkInfo]
    total: int
