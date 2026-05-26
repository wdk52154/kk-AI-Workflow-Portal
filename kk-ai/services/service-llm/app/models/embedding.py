"""Pydantic models for Embedding API."""

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Request body for embedding."""

    model: str | None = Field(
        default=None,
        description="ID of the model to use. Defaults to config default.",
    )
    input: str | list[str] = Field(
        ..., description="Input text to embed"
    )


class EmbeddingData(BaseModel):
    """A single embedding result."""

    object: str = "embedding"
    embedding: list[float]
    index: int


class EmbeddingUsage(BaseModel):
    """Usage statistics for the embedding request."""

    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    """Response from embedding request."""

    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingUsage
