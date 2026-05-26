"""API Key service for multi-project authentication."""

import json
import logging
import threading
import uuid
from typing import Optional

from app.config import get_settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.api_key")


class APIKey:
    """API Key entity for a project."""

    def __init__(
        self,
        key: str,
        project_id: str,
        name: str,
        rate_limit: int = 100,
        daily_quota: int = 10000,
        monthly_quota: int = 300000,
        status: str = "active",
    ):
        self.key = key
        self.project_id = project_id
        self.name = name
        self.rate_limit = rate_limit
        self.daily_quota = daily_quota
        self.monthly_quota = monthly_quota
        self.status = status

    def to_dict(self) -> dict:
        return {
            "api_key": self.key,
            "project_id": self.project_id,
            "name": self.name,
            "rate_limit_per_minute": self.rate_limit,
            "daily_quota": self.daily_quota,
            "monthly_quota": self.monthly_quota,
            "enabled": self.status == "active",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "APIKey":
        return cls(
            key=data.get("api_key", ""),
            project_id=data.get("project_id", ""),
            name=data.get("name", ""),
            rate_limit=data.get("rate_limit_per_minute", 100),
            daily_quota=data.get("daily_quota", 10000),
            monthly_quota=data.get("monthly_quota", 300000),
            status="active" if data.get("enabled", True) else "inactive",
        )


class APIKeyService:
    """Multi-project API Key management service (memory + Redis dual mode)."""

    def __init__(self):
        self._keys: dict[str, APIKey] = {}  # key -> APIKey
        self._lock = threading.Lock()
        self._load_default_keys()

    def _load_default_keys(self) -> None:
        """Load default keys from environment config."""
        settings = get_settings()
        if settings.API_KEYS_JSON:
            try:
                keys_data = json.loads(settings.API_KEYS_JSON)
                for kd in keys_data:
                    key = APIKey.from_dict(kd)
                    self._keys[key.key] = key
                logger.info("Loaded %d API keys from env", len(self._keys))
            except Exception:
                logger.exception("Failed to parse API_KEYS_JSON")

        # Preload admin key if not already present
        admin_key = settings.API_KEYS_JSON is None
        if admin_key:
            self._keys["kk-admin-key"] = APIKey(
                key="kk-admin-key",
                project_id="admin",
                name="Admin",
                rate_limit=1000,
                daily_quota=100000,
                monthly_quota=3000000,
                status="active",
            )
            logger.info("Loaded default admin API key")

    def validate(self, key: str) -> APIKey | None:
        """Validate API key. Return APIKey if valid, None otherwise."""
        api_key = self._keys.get(key)
        if api_key and api_key.status == "active":
            return api_key
        return None

    def create_key(
        self,
        project_id: str,
        name: str,
        rate_limit: int = 100,
        daily_quota: int = 10000,
        monthly_quota: int = 300000,
    ) -> APIKey:
        """Create a new API key."""
        with self._lock:
            key_str = f"kk-{uuid.uuid4().hex[:16]}"
            api_key = APIKey(
                key=key_str,
                project_id=project_id,
                name=name,
                rate_limit=rate_limit,
                daily_quota=daily_quota,
                monthly_quota=monthly_quota,
            )
            self._keys[key_str] = api_key
            logger.info("Created API key for project_id=%s", project_id)
            return api_key

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        with self._lock:
            if key in self._keys:
                self._keys[key].status = "inactive"
                logger.info("Revoked API key key_prefix=%s...", key[:8])
                return True
            return False

    def list_keys(self) -> list[APIKey]:
        """List all active API keys."""
        return [k for k in self._keys.values() if k.status == "active"]

    async def sync_from_redis(self) -> None:
        """Sync keys from Redis to memory."""
        redis_client = await get_redis_client()
        if not redis_client.is_connected:
            return

        try:
            data = await redis_client._redis.hgetall("mcp-hub:api-keys")  # type: ignore[union-attr]
            with self._lock:
                for key_str, value in data.items():
                    try:
                        kd = json.loads(value)
                        self._keys[key_str] = APIKey.from_dict(kd)
                    except Exception:
                        pass
            logger.info("Synced %d API keys from Redis", len(data))
        except Exception:
            logger.exception("Failed to sync API keys from Redis")

    async def save_to_redis(self, api_key: APIKey) -> None:
        """Save a key to Redis."""
        redis_client = await get_redis_client()
        if redis_client.is_connected:
            await redis_client._redis.hset(  # type: ignore[union-attr]
                "mcp-hub:api-keys",
                api_key.key,
                json.dumps(api_key.to_dict()),
            )


# Global singleton
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """Get or create the global APIKeyService instance."""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
