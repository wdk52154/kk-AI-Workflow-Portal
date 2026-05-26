"""Data query and export router."""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models import (
    CleanedDataItem,
    DataExportRequest,
    DataExportResponse,
    DataQueryRequest,
    DataQueryResponse,
)
from app.services.data_store import get_data_store

logger = logging.getLogger("service-data.router.query")
router = APIRouter()


def _parse_tags(tags_str: str | None) -> list[str] | None:
    """Parse tags from string to list."""
    if not tags_str:
        return None
    try:
        return json.loads(tags_str)
    except Exception:
        return tags_str.split(",") if tags_str else None


@router.post("/v1/data/query", response_model=DataQueryResponse)
async def query_data(body: DataQueryRequest):
    """Query cleaned data with filters."""
    store = get_data_store()

    rows, total = store.query_cleaned(
        source_type=body.source_type,
        project_id=body.project_id,
        date_from=body.date_from,
        date_to=body.date_to,
        intent=body.intent,
        emotion=body.emotion,
        tags=body.tags,
        min_quality_score=body.min_quality_score,
        status=body.status,
        page=body.page,
        page_size=body.page_size,
    )

    def _item_from_row(row: dict) -> CleanedDataItem:
        tags = []
        if row.get("tags"):
            try:
                tags = json.loads(row["tags"])
            except Exception:
                tags = []
        return CleanedDataItem(
            id=row["id"],
            raw_data_id=row["raw_data_id"],
            source_type=row["source_type"],
            project_id=row["project_id"],
            cleaned_content=row["cleaned_content"],
            quality_score=row["quality_score"],
            intent=row["intent"],
            emotion=row["emotion"],
            tags=tags,
            is_annotated=bool(row.get("is_annotated", 0)),
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    return DataQueryResponse(
        items=[_item_from_row(r) for r in rows],
        total=total,
        page=body.page,
        page_size=body.page_size,
    )


@router.post("/v1/data/export", response_model=DataExportResponse)
async def export_data(body: DataExportRequest):
    """Export cleaned data as JSON or CSV."""
    settings = get_settings()
    store = get_data_store()

    rows = store.export_cleaned(
        source_type=body.source_type,
        project_id=body.project_id,
        date_from=body.date_from,
        date_to=body.date_to,
        intent=body.intent,
        emotion=body.emotion,
        tags=body.tags,
        min_quality_score=body.min_quality_score,
        status=body.status,
        limit=settings.EXPORT_LIMIT,
    )

    if len(rows) > settings.EXPORT_LIMIT:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "EXPORT_TOO_LARGE",
                "message": f"Export exceeds limit of {settings.EXPORT_LIMIT} records",
            },
        )

    def _serialize_row(row: dict) -> dict:
        result = dict(row)
        for key in ["tags", "metadata", "annotation_data"]:
            if result.get(key):
                try:
                    result[key] = json.loads(result[key])
                except Exception:
                    pass
        return result

    data = [_serialize_row(r) for r in rows]

    return DataExportResponse(
        export_id=f"export_{uuid.uuid4().hex[:12]}",
        format=body.format,
        record_count=len(data),
        data=data,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
