"""Pydantic models for Model List API."""

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Information about a single model."""

    id: str = Field(..., description="The model identifier")
    object: str = "model"
    created: int = 0
    owned_by: str = "doubao"


class ModelListResponse(BaseModel):
    """Response from model list request."""

    object: str = "list"
    data: list[ModelInfo]
