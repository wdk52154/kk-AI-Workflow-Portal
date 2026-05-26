"""Memory store with hot (memory) and cold (SQLite) layers."""

import json
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import get_settings
from app.services.database import get_db_connection
from app.services.vector_index import vector_search

logger = logging.getLogger("service-memory.memory_store")


class MemoryStore:
    """Dual-layer memory store: hot (memory dict) + cold (SQLite)."""

    def __init__(self):
        settings = get_settings()
        self._hot: dict[str, dict] = {}  # memory_id -> entry
        self._ttl = timedelta(days=settings.HOT_DATA_TTL_DAYS)
        self._lock = threading.RLock()

    def store(self, entry: dict[str, Any]) -> str:
        """Store memory to both hot and cold storage."""
        memory_id = entry.get("memory_id") or f"mem_{uuid.uuid4().hex[:12]}"
        entry["memory_id"] = memory_id

        # Hot storage
        with self._lock:
            self._hot[memory_id] = dict(entry)

        # Cold storage (SQLite)
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (memory_id, session_id, user_id, role, content, embedding, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    content = excluded.content,
                    embedding = excluded.embedding,
                    timestamp = excluded.timestamp
                """,
                (
                    memory_id,
                    entry["session_id"],
                    entry["user_id"],
                    entry["role"],
                    entry["content"],
                    json.dumps(entry["embedding"]) if entry.get("embedding") else None,
                    entry["timestamp"],
                ),
            )
            conn.commit()

        logger.debug("Stored memory %s for session %s", memory_id, entry["session_id"])
        return memory_id

    def recall(
        self,
        session_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Recall memories from hot + cold storage."""
        # Collect from hot storage
        hot_entries = []
        with self._lock:
            for entry in self._hot.values():
                if entry.get("session_id") == session_id:
                    hot_entries.append(dict(entry))

        # Collect from cold storage
        cold_entries = []
        if len(hot_entries) < top_k:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM memories WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (session_id, top_k * 2),
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    if row_dict.get("embedding"):
                        row_dict["embedding"] = json.loads(row_dict["embedding"])
                    cold_entries.append(row_dict)

        # Merge and deduplicate
        seen_ids = {e["memory_id"] for e in hot_entries}
        all_entries = hot_entries[:]
        for entry in cold_entries:
            if entry["memory_id"] not in seen_ids:
                all_entries.append(entry)

        # Vector search
        return vector_search(all_entries, query_embedding, top_k)

    def list_by_session(self, session_id: str) -> list[dict[str, Any]]:
        """List all memories for a session."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM memories WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict.get("embedding"):
                    row_dict["embedding"] = json.loads(row_dict["embedding"])
                results.append(row_dict)
            return results

    def cleanup_expired(self) -> int:
        """Remove expired entries from hot storage."""
        cutoff = (datetime.now(timezone.utc) - self._ttl).isoformat()
        removed = 0
        with self._lock:
            expired = [
                mid for mid, entry in self._hot.items()
                if entry.get("timestamp", "") < cutoff
            ]
            for mid in expired:
                del self._hot[mid]
                removed += 1
        if removed:
            logger.info("Cleaned up %d expired hot memories", removed)
        return removed


# Global singleton
_memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get or create the global MemoryStore instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
