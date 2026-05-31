"""Asset storage service for CRUD and search operations."""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_db_connection
from app.services.storage import get_storage

logger = logging.getLogger("service-asset.asset_store")

_asset_store: "AssetStore | None" = None


class AssetStore:
    """SQLite-backed asset store with pluggable storage backend."""

    def __init__(self):
        settings = get_settings()
        self.storage_path = settings.STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        self.storage = get_storage()

    def _generate_asset_id(self) -> str:
        return f"asset_{uuid.uuid4().hex[:12]}"

    def _save_file(self, asset_id: str, file_data: bytes, filename: str) -> str:
        """Save file to storage backend and return storage key."""
        ext = os.path.splitext(filename)[1]
        storage_key = f"{asset_id[:8]}/{asset_id}{ext}"
        return self.storage.save(storage_key, file_data)

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
        """Update asset status with audit workflow tracking."""
        now = datetime.now(timezone.utc).isoformat()
        valid_statuses = ["uploaded", "precheck", "pending_review", "approved", "rejected"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        with get_db_connection() as conn:
            conn.execute(
                "UPDATE assets SET status = ?, updated_at = ? WHERE asset_id = ?",
                (status, now, asset_id),
            )
            conn.commit()
        return self.get_asset_by_id(asset_id)

    def run_precheck(self, asset_id: str) -> dict:
        """Run automated precheck (machine review) for uploaded asset.
        
        Simulates content safety check (NSFW/violence detection).
        In production, this would call an AI content moderation API.
        """
        asset = self.get_asset_by_id(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        if asset["status"] != "uploaded":
            raise ValueError(f"Cannot precheck asset with status: {asset['status']}")

        # Mock precheck: randomly approve or flag for review
        # In production: call content moderation API
        import random
        precheck_passed = random.random() > 0.1  # 90% pass rate

        if precheck_passed:
            return self.update_status(asset_id, "pending_review")
        else:
            return self.update_status(asset_id, "rejected")

    def approve_asset(self, asset_id: str) -> dict:
        """Manually approve asset after review."""
        asset = self.get_asset_by_id(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        if asset["status"] not in ["pending_review", "uploaded"]:
            raise ValueError(f"Cannot approve asset with status: {asset['status']}")
        return self.update_status(asset_id, "approved")

    def reject_asset(self, asset_id: str) -> dict:
        """Manually reject asset after review."""
        asset = self.get_asset_by_id(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        return self.update_status(asset_id, "rejected")

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
        """Get asset statistics including reuse rate."""
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

            # Reuse rate calculation
            cursor = conn.execute("SELECT COUNT(*) FROM assets WHERE usage_count > 0")
            reused_count = cursor.fetchone()[0]
            reuse_rate = round(reused_count / total_assets * 100, 1) if total_assets > 0 else 0.0

            # Average reuse multiplier (total usages / reused assets)
            cursor = conn.execute(
                "SELECT SUM(usage_count) FROM assets WHERE usage_count > 0"
            )
            total_usages = cursor.fetchone()[0] or 0
            avg_reuse_multiplier = round(total_usages / reused_count, 1) if reused_count > 0 else 0.0

            # Approved assets count
            cursor = conn.execute("SELECT COUNT(*) FROM assets WHERE status = 'approved'")
            approved_count = cursor.fetchone()[0]

        return {
            "total_assets": total_assets,
            "total_by_type": total_by_type,
            "total_by_status": total_by_status,
            "top_reused": top_reused,
            "recent_uploads": recent_uploads,
            "reuse_rate": reuse_rate,
            "avg_reuse_multiplier": avg_reuse_multiplier,
            "approved_count": approved_count,
            "reused_count": reused_count,
            "total_usages": total_usages,
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
