"""Pydantic models for data records, ingestion, query, and annotation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataRecord(BaseModel):
    """Single data record for ingestion."""

    raw_id: str = Field(..., description="Unique ID from source system")
    content: str = Field(..., min_length=1, max_length=10240, description="Raw content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Source metadata")


class DataIngestRequest(BaseModel):
    """Request model for data ingestion."""

    source_type: str = Field(
        ..., pattern=r"^(wechat|customer_service|sales_call|student_survey)$"
    )
    project_id: str = Field(..., min_length=1, max_length=64)
    records: list[DataRecord] = Field(..., min_length=1)


class DataIngestResponse(BaseModel):
    """Response model for data ingestion."""

    batch_id: str
    record_count: int
    success_count: int
    failed_count: int
    status: str
    message: str


class DataQueryRequest(BaseModel):
    """Request model for data query."""

    source_type: str | None = None
    project_id: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    intent: str | None = None
    emotion: str | None = None
    tags: list[str] | None = None
    min_quality_score: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CleanedDataItem(BaseModel):
    """Single cleaned data item in query response."""

    id: int
    raw_data_id: int
    source_type: str
    project_id: str
    cleaned_content: str
    quality_score: int | None
    intent: str | None
    emotion: str | None
    tags: list[str]
    is_annotated: bool
    status: str
    created_at: str
    updated_at: str


class DataQueryResponse(BaseModel):
    """Response model for data query."""

    items: list[CleanedDataItem]
    total: int
    page: int
    page_size: int


class DataExportRequest(BaseModel):
    """Request model for data export."""

    format: str = Field(default="json", pattern=r"^(json|csv)$")
    source_type: str | None = None
    project_id: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    intent: str | None = None
    emotion: str | None = None
    tags: list[str] | None = None
    min_quality_score: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None


class DataExportResponse(BaseModel):
    """Response model for data export."""

    export_id: str
    format: str
    record_count: int
    data: list[dict[str, Any]]
    generated_at: str


class AnnotationRequest(BaseModel):
    """Request model for manual annotation."""

    intent: str | None = None
    emotion: str | None = None
    quality_score: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None
    notes: str | None = None


class AnnotationResponse(BaseModel):
    """Response model for annotation."""

    record_id: int
    annotation_id: int
    status: str
    message: str


class PendingAnnotationItem(BaseModel):
    """Single pending annotation item."""

    id: int
    raw_data_id: int
    cleaned_content: str
    quality_score: int | None
    created_at: str


class PendingAnnotationResponse(BaseModel):
    """Response model for pending annotations."""

    items: list[PendingAnnotationItem]
    total: int
    page: int
    page_size: int


class AnnotationStatsResponse(BaseModel):
    """Response model for annotation statistics."""

    total_records: int
    annotated_count: int
    pending_count: int
    annotation_rate: float
    intent_distribution: dict[str, int]
    emotion_distribution: dict[str, int]
    tag_distribution: dict[str, int]


class RecordsBySource(BaseModel):
    """Record count by source type."""

    source_type: str
    count: int


class RecordsByProject(BaseModel):
    """Record count by project."""

    project_id: str
    count: int


class TopIntent(BaseModel):
    """Top intent with count."""

    intent: str
    count: int


class DataGrowthItem(BaseModel):
    """Daily data growth item."""

    date: str
    count: int


class DataStatsResponse(BaseModel):
    """Response model for data dashboard statistics."""

    total_records: int
    total_cleaned: int
    total_annotated: int
    records_by_source: list[RecordsBySource]
    records_by_project: list[RecordsByProject]
    avg_quality_score: float
    annotation_progress: dict[str, int]
    top_intents: list[TopIntent]
    emotion_distribution: dict[str, int]
    data_growth: list[DataGrowthItem]
