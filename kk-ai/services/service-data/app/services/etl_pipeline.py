"""ETL Pipeline: deduplicate, desensitize, normalize, quality score."""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone

from app.config import get_settings
from app.services.data_store import get_data_store
from app.services.database import get_db_connection
from app.services.rag_client import get_rag_client

logger = logging.getLogger("service-data.etl")

# Desensitization patterns (longer patterns first to avoid overlap)
SENSITIVE_PATTERNS = [
    (r'\d{17}[\dXx]', '[ID]'),  # ID first (18 digits) to avoid partial phone match
    (r'1[3-9]\d{9}', '[PHONE]'),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
]


class ETLPipeline:
    """ETL pipeline for processing raw data into cleaned data."""

    async def process_batch(self, batch_id: str) -> dict:
        """Process a batch of raw data."""
        store = get_data_store()
        raw_records = store.get_raw_by_batch(batch_id, status='pending')

        results = {'cleaned': 0, 'duplicated': 0, 'failed': 0}

        for record in raw_records:
            try:
                # Step 1: Deduplication
                content_hash = self._hash_content(record['content'])
                if store.is_duplicate(record['project_id'], content_hash):
                    store.update_raw_status(record['id'], 'duplicated')
                    results['duplicated'] += 1
                    continue

                # Step 2: Desensitization
                cleaned = self._desensitize(record['content'])

                # Step 3: Normalization
                cleaned = self._normalize(cleaned)

                # Step 4: Quality scoring
                quality_score = self._calculate_quality_score(cleaned)

                # Save cleaned data
                store.save_cleaned({
                    'raw_data_id': record['id'],
                    'source_type': record['source_type'],
                    'project_id': record['project_id'],
                    'original_content': record['content'],
                    'cleaned_content': cleaned,
                    'content_hash': content_hash,
                    'quality_score': quality_score,
                })
                store.update_raw_status(record['id'], 'cleaned')
                results['cleaned'] += 1

            except Exception as exc:
                logger.error("ETL failed for record %s: %s", record['id'], exc)
                store.update_raw_status(record['id'], 'failed')
                results['failed'] += 1

        # Update batch status
        store.update_batch_status(batch_id, 'completed', results)

        # Auto-vectorize high-quality data
        await self._auto_vectorize(batch_id)

        return results

    def _hash_content(self, content: str) -> str:
        """Generate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

    def _desensitize(self, content: str) -> str:
        """Remove sensitive information from content."""
        for pattern, replacement in SENSITIVE_PATTERNS:
            content = re.sub(pattern, replacement, content)
        return content

    def _normalize(self, content: str) -> str:
        """Normalize content formatting."""
        # Keep printable chars and newlines/tabs
        content = ''.join(c for c in content if c.isprintable() or c in '\n\t')
        # Normalize newlines
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # Strip extra whitespace per line, remove empty lines
        lines = [line.strip() for line in content.split('\n')]
        return '\n'.join(line for line in lines if line)

    def _calculate_quality_score(self, content: str) -> int:
        """Calculate a quality score for the content."""
        score = 50
        length = len(content)

        if length > 20:
            score += 20
        if length > 50:
            score += 15
        # Has sentence-ending punctuation (Chinese or English)
        if any(c in content for c in '。？！.?!'):
            score += 10
        # Has structured content (numbers, lists)
        if re.search(r'\d+', content):
            score += 5

        return min(100, score)

    async def _auto_vectorize(self, batch_id: str) -> None:
        """Auto-vectorize high-quality cleaned data from this batch."""
        settings = get_settings()
        store = get_data_store()

        # Get cleaned records from this batch that meet quality threshold
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT cd.id, cd.cleaned_content, cd.project_id, cd.source_type, cd.intent, cd.tags
                FROM cleaned_data cd
                JOIN raw_data rd ON cd.raw_data_id = rd.id
                WHERE rd.batch_id = ? AND cd.quality_score >= ? AND cd.status = 'available'
                """,
                (batch_id, settings.QUALITY_THRESHOLD),
            )
            records = cursor.fetchall()

        if not records:
            return

        rag_client = get_rag_client()
        for row in records:
            try:
                tags = json.loads(row['tags']) if row['tags'] else []
                metadata = {
                    "source_type": row['source_type'],
                    "project_id": row['project_id'],
                    "intent": row['intent'] or "",
                    "tags": tags,
                    "cleaned_data_id": row['id'],
                }
                await rag_client.ingest_document(
                    content=row['cleaned_content'],
                    metadata=metadata,
                    doc_id=f"data_{row['id']}",
                )
                # Mark as vectorized
                with get_db_connection() as conn:
                    conn.execute(
                        "UPDATE cleaned_data SET status = 'vectorized' WHERE id = ?",
                        (row['id'],),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning("Auto-vectorize failed for record %s: %s", row['id'], exc)
