"""Asset storage service for CRUD and search operations."""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_db_connection

logger = logging.getLogger("service-asset.asset_store")

_asset_store: "AssetStore | None" = None


class AssetStore:
    """SQLite-backed asset store with file system storage."""

    def __init__(self):
        settings = get_settings()
        self.storage_path = settings.STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)

    def _generate_asset_id(self) -> str:
        return f"asset_{uuid.uuid4().hex[:12]}"

    def _save_file(self, asset_id: str, file_data: bytes, filename: str) -> str:
        """Save file to storage and return relative path."""
        ext = os.path.splitext(filename)[1]
        subdir = os.path.join(self.storage_path, asset_id[:8])
        os.makedirs(subdir, exist_ok=True)
        file_path = os.path.join(subdir, f"{asset_id}{ext}")
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path

    def create_asset(
        self,
        name: str,
        asset_type: str,
        file_data: bytes,
        filename: str,
        mime_type: str,
        description: str = "",
        tags: list[str] | None = None,
        category: str = "",
    ) -> dict:
        """Create a new asset record and save file."""
        asset_id = self._generate_asset_id()
        file_path = self._save_file(asset_id, file_data, filename)
        file_size = len(file_data)
        now = datetime.now(timezone.utc).isoformat()

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO assets (asset_id, name, asset_type, file_path, file_size, mime_type,
                    description, tags, category, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    name,
                    asset_type,
                    file_path,
                    file_size,
                    mime_type,
                    description,
                    json.dumps(tags or []),
                    category,
                    "uploaded",
                    now,
                    now,
                ),
            )
            conn.commit()

        logger.info("Created asset %s (%s)", asset_id, name)
        return self.get_asset_by_id(asset_id)

    def get_asset_by_id(self, asset_id: str) -> dict | None:
        """Get asset by asset_id."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM assets WHERE asset_id = ?",
                (asset_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def search_assets(
        self,
        q: str | None = None,
        asset_type: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Search assets with filters."""
        conditions = ["1=1"]
        params: list = []

        if q:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if asset_type:
            conditions.append("asset_type = ?")
            params.append(asset_type)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions)
        offset = (page - 1) * page_size

        with get_db_connection() as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM assets WHERE {where_clause}",
                params,
            )
            total = cursor.fetchone()[0]

            # Tags filter in Python (SQLite doesn't support JSON array contains easily)
            cursor = conn.execute(
                f"SELECT * FROM assets WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            )
            rows = cursor.fetchall()
            items = [self._row_to_dict(r) for r in rows]

            if tags:
                items = [i for i in items if any(t in i.get("tags", []) for t in tags)]
                total = len(items)

        return items, total

    def update_status(self, asset_id: str, status: str) -> dict | None:
        """Update asset status."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE assets SET status = ?, updated_at = ? WHERE asset_id = ?",
                (status, now, asset_id),
            )
            conn.commit()
        return self.get_asset_by_id(asset_id)

    def record_usage(self, asset_id: str, project_id: str | None = None, action: str = "download") -> None:
        """Record asset usage."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO asset_usage (asset_id, project_id, action, created_at) VALUES (?, ?, ?, ?)",
                (asset_id, project_id, action, now),
            )
            conn.execute(
                "UPDATE assets SET usage_count = usage_count + 1 WHERE asset_id = ?",
                (asset_id,),
            )
            conn.commit()

    def get_stats(self) -> dict:
        """Get asset statistics."""
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM assets")
            total_assets = cursor.fetchone()[0]

            cursor = conn.execute("SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type")
            total_by_type = {r[0]: r[1] for r in cursor.fetchall()}

            cursor = conn.execute("SELECT status, COUNT(*) FROM assets GROUP BY status")
            total_by_status = {r[0]: r[1] for r in cursor.fetchall()}

            cursor = conn.execute(
                "SELECT asset_id, name, usage_count FROM assets ORDER BY usage_count DESC LIMIT 5"
            )
            top_reused = [{"asset_id": r[0], "name": r[1], "usage_count": r[2]} for r in cursor.fetchall()]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM assets WHERE created_at >= date('now', '-7 days')"
            )
            recent_uploads = cursor.fetchone()[0]

        return {
            "total_assets": total_assets,
            "total_by_type": total_by_type,
            "total_by_status": total_by_status,
            "top_reused": top_reused,
            "recent_uploads": recent_uploads,
        }

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        result = dict(row)
        for key in ["tags", "project_ids"]:
            if result.get(key):
                try:
                    result[key] = json.loads(result[key])
                except Exception:
                    result[key] = []
            else:
                result[key] = []
        return result


def get_asset_store() -> AssetStore:
    """Get singleton AssetStore instance."""
    global _asset_store
    if _asset_store is None:
        _asset_store = AssetStore()
    return _asset_store
