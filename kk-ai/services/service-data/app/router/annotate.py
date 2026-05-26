"""Annotation router."""

import logging

from fastapi import APIRouter, HTTPException

from app.models import (
    AnnotationRequest,
    AnnotationResponse,
    AnnotationStatsResponse,
    PendingAnnotationItem,
    PendingAnnotationResponse,
)
from app.services.data_store import get_data_store

logger = logging.getLogger("service-data.router.annotate")
router = APIRouter()


@router.post("/v1/data/{record_id}/annotate", response_model=AnnotationResponse)
async def annotate_record(record_id: int, body: AnnotationRequest):
    """Annotate a cleaned data record."""
    store = get_data_store()
    record = store.get_cleaned_by_id(record_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "RECORD_NOT_FOUND", "message": f"Record {record_id} not found"},
        )

    annotation = {
        "intent": body.intent,
        "emotion": body.emotion,
        "quality_score": body.quality_score,
        "tags": body.tags or [],
        "notes": body.notes,
    }

    store.annotate_record(record_id, annotation)

    return AnnotationResponse(
        record_id=record_id,
        annotation_id=record_id,
        status="annotated",
        message="Annotation saved successfully",
    )


@router.get("/v1/data/pending_annotation", response_model=PendingAnnotationResponse)
async def get_pending_annotation(project_id: str | None = None, page: int = 1, page_size: int = 20):
    """Get records pending annotation, ordered by quality score ascending."""
    store = get_data_store()
    items, total = store.get_pending_annotations(project_id=project_id, page=page, page_size=page_size)

    return PendingAnnotationResponse(
        items=[
            PendingAnnotationItem(
                id=item["id"],
                raw_data_id=item["raw_data_id"],
                cleaned_content=item["cleaned_content"],
                quality_score=item["quality_score"],
                created_at=item["created_at"],
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/v1/data/annotation_stats", response_model=AnnotationStatsResponse)
async def get_annotation_stats(project_id: str | None = None):
    """Get annotation statistics."""
    store = get_data_store()
    stats = store.get_annotation_stats(project_id=project_id)

    return AnnotationStatsResponse(
        total_records=stats["total_records"],
        annotated_count=stats["annotated_count"],
        pending_count=stats["pending_count"],
        annotation_rate=stats["annotation_rate"],
        intent_distribution=stats["intent_distribution"],
        emotion_distribution=stats["emotion_distribution"],
        tag_distribution=stats["tag_distribution"],
    )
