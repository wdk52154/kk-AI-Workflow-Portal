"""Data dashboard statistics router."""

import logging

from fastapi import APIRouter

from app.models import DataStatsResponse
from app.services.data_store import get_data_store

logger = logging.getLogger("service-data.router.stats")
router = APIRouter()


@router.get("/v1/data/stats", response_model=DataStatsResponse)
async def get_data_stats():
    """Get data dashboard statistics."""
    store = get_data_store()
    stats = store.get_data_stats()

    return DataStatsResponse(
        total_records=stats["total_records"],
        total_cleaned=stats["total_cleaned"],
        total_annotated=stats["total_annotated"],
        records_by_source=stats["records_by_source"],
        records_by_project=stats["records_by_project"],
        avg_quality_score=stats["avg_quality_score"],
        annotation_progress=stats["annotation_progress"],
        top_intents=stats["top_intents"],
        emotion_distribution=stats["emotion_distribution"],
        data_growth=stats["data_growth"],
    )
