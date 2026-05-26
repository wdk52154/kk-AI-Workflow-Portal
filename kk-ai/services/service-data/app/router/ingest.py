"""Data ingestion router."""

import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models import DataIngestRequest, DataIngestResponse
from app.services.data_store import get_data_store
from app.services.etl_pipeline import ETLPipeline

logger = logging.getLogger("service-data.router.ingest")
router = APIRouter()


@router.post("/v1/data/ingest", response_model=DataIngestResponse)
async def ingest_data(body: DataIngestRequest):
    """Ingest raw data records into the data center."""
    settings = get_settings()

    if len(body.records) > settings.BATCH_SIZE_LIMIT:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "BATCH_TOO_LARGE",
                "message": f"Batch size exceeds limit of {settings.BATCH_SIZE_LIMIT}",
            },
        )

    store = get_data_store()

    # Create batch record
    batch_id = store.create_batch(body.source_type, body.project_id, len(body.records))

    # Prepare records with content hash
    import hashlib
    records_to_save = []
    for rec in body.records:
        content_hash = hashlib.md5(rec.content.encode('utf-8')).hexdigest()[:16]
        records_to_save.append({
            "raw_id": rec.raw_id,
            "content": rec.content,
            "content_hash": content_hash,
            "metadata": rec.metadata,
        })

    # Save raw records
    success_count, failed_count = store.save_raw_records(
        batch_id, body.source_type, body.project_id, records_to_save
    )

    # Run ETL pipeline asynchronously
    etl = ETLPipeline()
    try:
        etl_results = await etl.process_batch(batch_id)
        status = "completed"
        message = f"ETL completed: {etl_results['cleaned']} cleaned, {etl_results['duplicated']} duplicated, {etl_results['failed']} failed"
    except Exception as exc:
        logger.error("ETL pipeline failed for batch %s: %s", batch_id, exc)
        status = "etl_failed"
        message = f"ETL failed: {str(exc)}"
        store.update_batch_status(batch_id, "etl_failed")

    return DataIngestResponse(
        batch_id=batch_id,
        record_count=len(body.records),
        success_count=success_count,
        failed_count=failed_count,
        status=status,
        message=message,
    )
