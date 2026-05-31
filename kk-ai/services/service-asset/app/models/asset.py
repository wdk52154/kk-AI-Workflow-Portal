"""Pydantic models for asset management."""

from typing import Any

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field(..., pattern=r"^(image|video|poster_template)$")
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""


class AssetItem(BaseModel):
    id: int
    asset_id: str
    name: str
    asset_type: str
    file_path: str
    file_size: int
    mime_type: str
    description: str
    tags: list[str]
    category: str
    status: str
    usage_count: int
    project_ids: list[str]
    created_at: str
    updated_at: str


class AssetListResponse(BaseModel):
    items: list[AssetItem]
    total: int


class AssetSearchRequest(BaseModel):
    q: str | None = None
    asset_type: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PosterGenerateRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


class PosterGenerateResponse(BaseModel):
    asset_id: str
    download_url: str
    message: str


class AssetStatsResponse(BaseModel):
    total_assets: int
    total_by_type: dict[str, int]
    total_by_status: dict[str, int]
    top_reused: list[dict[str, Any]]
    recent_uploads: int
