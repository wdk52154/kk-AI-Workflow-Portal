"""Data storage service for raw, cleaned, and batch data."""

import json
import logging
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.services.database import get_db_connection

logger = logging.getLogger("service-data.data_store")

_data_store: "DataStore | None" = None


class DataStore:
    """SQLite-backed data store for raw and cleaned data."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_settings().DB_PATH

    def create_batch(self, source_type: str, project_id: str, record_count: int) -> str:
        """Create a new batch record."""
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO data_batches (batch_id, source_type, project_id, record_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (batch_id, source_type, project_id, record_count, now),
            )
            conn.commit()
        return batch_id

    def save_raw_records(
        self, batch_id: str, source_type: str, project_id: str, records: list[dict]
    ) -> tuple[int, int]:
        """Save raw records. Returns (success_count, failed_count)."""
        success = 0
        failed = 0
        now = datetime.now(timezone.utc).isoformat()

        with get_db_connection(self.db_path) as conn:
            for rec in records:
                try:
                    conn.execute(
                        """
                        INSERT INTO raw_data (raw_id, source_type, project_id, content, content_hash, metadata, batch_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rec["raw_id"],
                            source_type,
                            project_id,
                            rec["content"],
                            rec.get("content_hash", ""),
                            json.dumps(rec.get("metadata", {})),
                            batch_id,
                            now,
                        ),
                    )
                    success += 1
                except Exception as exc:
                    logger.warning("Failed to insert raw record %s: %s", rec.get("raw_id"), exc)
                    failed += 1
            conn.commit()

        # Update batch counts
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE data_batches SET success_count = ?, failed_count = ? WHERE batch_id = ?
                """,
                (success, failed, batch_id),
            )
            conn.commit()

        return success, failed

    def get_raw_by_batch(self, batch_id: str, status: str = "pending") -> list[dict]:
        """Get raw records by batch ID and status."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM raw_data WHERE batch_id = ? AND status = ?",
                (batch_id, status),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def is_duplicate(self, project_id: str, content_hash: str) -> bool:
        """Check if content hash already exists in cleaned_data for this project."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM cleaned_data WHERE project_id = ? AND content_hash = ? LIMIT 1",
                (project_id, content_hash),
            )
            return cursor.fetchone() is not None

    def update_raw_status(self, raw_id: int, status: str, error: str | None = None) -> None:
        """Update raw data status."""
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE raw_data SET status = ? WHERE id = ?",
                (status, raw_id),
            )
            conn.commit()

    def save_cleaned(self, data: dict) -> int:
        """Save cleaned data. Returns cleaned_data id."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO cleaned_data (
                    raw_data_id, source_type, project_id, original_content,
                    cleaned_content, content_hash, quality_score, intent, emotion,
                    tags, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["raw_data_id"],
                    data["source_type"],
                    data["project_id"],
                    data["original_content"],
                    data["cleaned_content"],
                    data["content_hash"],
                    data.get("quality_score"),
                    data.get("intent"),
                    data.get("emotion"),
                    json.dumps(data.get("tags", [])),
                    data.get("status", "available"),
                    now,
                    now,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_cleaned_by_id(self, record_id: int) -> dict | None:
        """Get cleaned data by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM cleaned_data WHERE id = ?",
                (record_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def annotate_record(self, record_id: int, annotation: dict) -> int:
        """Annotate a cleaned record. Returns annotation record id."""
        now = datetime.now(timezone.utc).isoformat()
        tags = annotation.get("tags", [])
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE cleaned_data SET
                    intent = COALESCE(?, intent),
                    emotion = COALESCE(?, emotion),
                    tags = ?,
                    is_annotated = 1,
                    annotation_data = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    annotation.get("intent"),
                    annotation.get("emotion"),
                    json.dumps(tags),
                    json.dumps(annotation),
                    now,
                    record_id,
                ),
            )
            conn.commit()
        return record_id

    def get_pending_annotations(
        self, project_id: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """Get pending annotation records ordered by quality score ascending."""
        offset = (page - 1) * page_size
        where = "is_annotated = 0 AND status = 'available'"
        params: list = []
        if project_id:
            where += " AND project_id = ?"
            params.append(project_id)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM cleaned_data WHERE {where}",
                params,
            )
            total = cursor.fetchone()[0]

            cursor = conn.execute(
                f"""
                SELECT id, raw_data_id, cleaned_content, quality_score, created_at
                FROM cleaned_data
                WHERE {where}
                ORDER BY quality_score ASC, created_at ASC
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset],
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows], total

    def get_annotation_stats(self, project_id: str | None = None) -> dict:
        """Get annotation statistics."""
        where = "1=1"
        params: list = []
        if project_id:
            where += " AND project_id = ?"
            params.append(project_id)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM cleaned_data WHERE {where}", params
            )
            total_records = cursor.fetchone()[0]

            cursor = conn.execute(
                f"SELECT COUNT(*) FROM cleaned_data WHERE is_annotated = 1 AND {where}",
                params,
            )
            annotated_count = cursor.fetchone()[0]

            cursor = conn.execute(
                f"SELECT intent, COUNT(*) as cnt FROM cleaned_data WHERE intent IS NOT NULL AND {where} GROUP BY intent",
                params,
            )
            intent_distribution = {r[0]: r[1] for r in cursor.fetchall()}

            cursor = conn.execute(
                f"SELECT emotion, COUNT(*) as cnt FROM cleaned_data WHERE emotion IS NOT NULL AND {where} GROUP BY emotion",
                params,
            )
            emotion_distribution = {r[0]: r[1] for r in cursor.fetchall()}

            cursor = conn.execute(
                f"SELECT tags FROM cleaned_data WHERE tags IS NOT NULL AND tags != '[]' AND {where}",
                params,
            )
            tag_counts: dict[str, int] = {}
            for row in cursor.fetchall():
                tags = json.loads(row[0])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_records": total_records,
            "annotated_count": annotated_count,
            "pending_count": total_records - annotated_count,
            "annotation_rate": round(annotated_count / total_records, 4) if total_records else 0.0,
            "intent_distribution": intent_distribution,
            "emotion_distribution": emotion_distribution,
            "tag_distribution": tag_counts,
        }

    def query_cleaned(
        self,
        source_type: str | None = None,
        project_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        intent: str | None = None,
        emotion: str | None = None,
        tags: list[str] | None = None,
        min_quality_score: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Query cleaned data with filters."""
        conditions = ["1=1"]
        params: list = []

        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        if intent:
            conditions.append("intent = ?")
            params.append(intent)
        if emotion:
            conditions.append("emotion = ?")
            params.append(emotion)
        if min_quality_score is not None:
            conditions.append("quality_score >= ?")
            params.append(min_quality_score)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions)
        offset = (page - 1) * page_size

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM cleaned_data WHERE {where_clause}",
                params,
            )
            total = cursor.fetchone()[0]

            cursor = conn.execute(
                f"""
                SELECT * FROM cleaned_data
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset],
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows], total

    def export_cleaned(
        self,
        source_type: str | None = None,
        project_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        intent: str | None = None,
        emotion: str | None = None,
        tags: list[str] | None = None,
        min_quality_score: int | None = None,
        status: str | None = None,
        limit: int = 10000,
    ) -> list[dict]:
        """Export cleaned data with filters."""
        conditions = ["1=1"]
        params: list = []

        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
        if intent:
            conditions.append("intent = ?")
            params.append(intent)
        if emotion:
            conditions.append("emotion = ?")
            params.append(emotion)
        if min_quality_score is not None:
            conditions.append("quality_score >= ?")
            params.append(min_quality_score)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT * FROM cleaned_data
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params + [limit],
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_data_stats(self) -> dict:
        """Get dashboard statistics."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM raw_data")
            total_raw = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM cleaned_data")
            total_cleaned = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM cleaned_data WHERE is_annotated = 1"
            )
            total_annotated = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT source_type, COUNT(*) as cnt FROM raw_data GROUP BY source_type"
            )
            records_by_source = [{"source_type": r[0], "count": r[1]} for r in cursor.fetchall()]

            cursor = conn.execute(
                "SELECT project_id, COUNT(*) as cnt FROM raw_data GROUP BY project_id"
            )
            records_by_project = [{"project_id": r[0], "count": r[1]} for r in cursor.fetchall()]

            cursor = conn.execute(
                "SELECT AVG(quality_score) FROM cleaned_data WHERE quality_score IS NOT NULL"
            )
            avg_quality = cursor.fetchone()[0] or 0.0

            cursor = conn.execute(
                "SELECT intent, COUNT(*) as cnt FROM cleaned_data WHERE intent IS NOT NULL GROUP BY intent ORDER BY cnt DESC LIMIT 10"
            )
            top_intents = [{"intent": r[0], "count": r[1]} for r in cursor.fetchall()]

            cursor = conn.execute(
                "SELECT emotion, COUNT(*) as cnt FROM cleaned_data WHERE emotion IS NOT NULL GROUP BY emotion"
            )
            emotion_distribution = {r[0]: r[1] for r in cursor.fetchall()}

            cursor = conn.execute(
                """
                SELECT date(created_at) as dt, COUNT(*) as cnt
                FROM raw_data
                WHERE created_at >= date('now', '-7 days')
                GROUP BY dt
                ORDER BY dt ASC
                """
            )
            data_growth = [{"date": r[0], "count": r[1]} for r in cursor.fetchall()]

        return {
            "total_records": total_raw,
            "total_cleaned": total_cleaned,
            "total_annotated": total_annotated,
            "records_by_source": records_by_source,
            "records_by_project": records_by_project,
            "avg_quality_score": round(avg_quality, 2) if avg_quality else 0.0,
            "annotation_progress": {
                "annotated": total_annotated,
                "pending": total_cleaned - total_annotated,
                "total": total_cleaned,
            },
            "top_intents": top_intents,
            "emotion_distribution": emotion_distribution,
            "data_growth": data_growth,
        }

    def get_batch_status(self, batch_id: str) -> dict | None:
        """Get batch status."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM data_batches WHERE batch_id = ?",
                (batch_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_batch_status(self, batch_id: str, status: str, results: dict | None = None) -> None:
        """Update batch status."""
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE data_batches SET status = ? WHERE batch_id = ?",
                (status, batch_id),
            )
            conn.commit()


def get_data_store() -> DataStore:
    """Get singleton DataStore instance."""
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
    return _data_store
