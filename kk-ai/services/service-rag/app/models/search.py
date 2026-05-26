"""Pydantic models for knowledge search."""

from typing import Any

from pydantic import BaseModel, Field


class SearchKnowledgeRequest(BaseModel):
    """Request body for knowledge search."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    rerank: bool = Field(default=False, description="Enable LLM reranking")
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Metadata filters (source_type, tags, date_range)",
    )


class SearchResultItem(BaseModel):
    """A single search result."""

    content: str
    score: float = Field(..., description="Similarity score (1 - distance)")
    rerank_score: float | None = Field(default=None, description="Rerank score if enabled")
    metadata: dict[str, Any]


class SearchKnowledgeResponse(BaseModel):
    """Response from knowledge search."""

    query: str
    results: list[SearchResultItem]
    total: int
    reranked: bool = False
