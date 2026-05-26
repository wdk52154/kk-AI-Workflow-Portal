"""User fact store - global cross-project user profile storage."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.database import get_db_connection
from app.services.vector_index import vector_search

logger = logging.getLogger("service-memory.user_fact_store")


class UserFactStore:
    """Global user fact store (shared across all projects)."""

    def store(self, fact: dict[str, Any]) -> str:
        """Store or update a user fact."""
        fact_id = fact.get("fact_id") or f"fact_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_facts
                (fact_id, user_id, fact_type, fact_content, embedding, confidence,
                 source_project_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, fact_type, fact_content) DO UPDATE SET
                    confidence = excluded.confidence,
                    embedding = excluded.embedding,
                    updated_at = excluded.updated_at,
                    source_project_id = excluded.source_project_id,
                    fact_id = excluded.fact_id
                """,
                (
                    fact_id,
                    fact["user_id"],
                    fact["fact_type"],
                    fact["fact_content"],
                    json.dumps(fact["embedding"]) if fact.get("embedding") else None,
                    fact["confidence"],
                    fact["source_project_id"],
                    fact.get("created_at", now),
                    now,
                ),
            )
            conn.commit()

        logger.debug("Stored fact %s for user %s", fact_id, fact["user_id"])
        return fact_id

    def recall(
        self,
        user_id: str,
        fact_type: str | None = None,
        query_embedding: list[float] | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Recall user facts. Optional semantic search with query_embedding."""
        with get_db_connection() as conn:
            sql = "SELECT * FROM user_facts WHERE user_id = ?"
            params = [user_id]

            if fact_type:
                sql += " AND fact_type = ?"
                params.append(fact_type)

            sql += " ORDER BY confidence DESC"

            cursor = conn.execute(sql, params)
            facts = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict.get("embedding"):
                    row_dict["embedding"] = json.loads(row_dict["embedding"])
                facts.append(row_dict)

        if query_embedding and facts:
            return vector_search(facts, query_embedding, top_k)

        return facts[:top_k]

    def list_by_user(self, user_id: str) -> list[dict[str, Any]]:
        """List all facts for a user."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_facts WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict.get("embedding"):
                    row_dict["embedding"] = json.loads(row_dict["embedding"])
                results.append(row_dict)
            return results


# Global singleton
_user_fact_store: UserFactStore | None = None


def get_user_fact_store() -> UserFactStore:
    """Get or create the global UserFactStore instance."""
    global _user_fact_store
    if _user_fact_store is None:
        _user_fact_store = UserFactStore()
    return _user_fact_store
