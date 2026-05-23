"""Redis client wrapper with connection pooling."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger("mcp-hub.redis")


class RedisClient:
    """Async Redis client wrapper for gateway operations."""

    _instance: Optional["RedisClient"] = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> redis.Redis:
        """Initialize Redis connection."""
        if self._redis is not None:
            return self._redis

        settings = get_settings()
        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("Redis connected: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning("Redis connection failed (%s), falling back to memory", exc)
            self._redis = None
        return self._redis  # type: ignore[return-value]

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    # --- Rate Limit: Sliding Window ---

    async def check_rate_limit(
        self,
        project_id: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check sliding window rate limit.
        Returns (allowed, current_count, limit).
        """
        if not self._redis:
            return True, 0, limit

        now = datetime.now(timezone.utc).timestamp()
        key = f"ratelimit:{project_id}:{endpoint}"
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1] + 1  # +1 for the current request
        allowed = current_count <= limit

        if not allowed:
            # Rollback the added entry if over limit
            await self._redis.zrem(key, str(now))
            current_count -= 1

        return allowed, current_count, limit

    # --- Quota: Daily / Monthly ---

    async def check_and_consume_quota(
        self,
        project_id: str,
        daily_quota: int,
        monthly_quota: int,
    ) -> tuple[bool, dict]:
        """
        Check and consume quota. Returns (allowed, quota_info).
        """
        if not self._redis:
            return True, {"daily_used": 0, "daily_limit": daily_quota, "monthly_used": 0, "monthly_limit": monthly_quota}

        now = datetime.now(timezone.utc)
        day_key = now.strftime("quota:daily:%Y%m%d")
        month_key = now.strftime("quota:monthly:%Y%m")

        daily_key = f"{day_key}:{project_id}"
        monthly_key = f"{month_key}:{project_id}"

        pipe = self._redis.pipeline()
        pipe.get(daily_key)
        pipe.get(monthly_key)
        results = await pipe.execute()

        daily_used = int(results[0] or 0)
        monthly_used = int(results[1] or 0)

        if daily_used >= daily_quota:
            return False, {
                "daily_used": daily_used,
                "daily_limit": daily_quota,
                "monthly_used": monthly_used,
                "monthly_limit": monthly_quota,
                "reason": "daily_quota_exceeded",
            }

        if monthly_used >= monthly_quota:
            return False, {
                "daily_used": daily_used,
                "daily_limit": daily_quota,
                "monthly_used": monthly_used,
                "monthly_limit": monthly_quota,
                "reason": "monthly_quota_exceeded",
            }

        # Consume quota
        pipe = self._redis.pipeline()
        pipe.incr(daily_key)
        pipe.incr(monthly_key)
        # Expire: daily at end of day + 1h buffer, monthly at end of month + 1d buffer
        pipe.expire(daily_key, 25 * 3600)
        pipe.expire(monthly_key, 32 * 24 * 3600)
        await pipe.execute()

        return True, {
            "daily_used": daily_used + 1,
            "daily_limit": daily_quota,
            "monthly_used": monthly_used + 1,
            "monthly_limit": monthly_quota,
        }

    # --- Auth: API Key -> Project ---

    async def get_project_by_api_key(self, api_key: str) -> Optional[dict]:
        """Lookup project info by API key."""
        if not self._redis:
            return None

        data = await self._redis.hget("mcp-hub:api-keys", api_key)
        if data:
            return json.loads(data)
        return None

    async def set_project_api_key(self, api_key: str, project: dict) -> None:
        """Register an API key for a project."""
        if self._redis:
            await self._redis.hset("mcp-hub:api-keys", api_key, json.dumps(project))

    async def delete_project_api_key(self, api_key: str) -> None:
        if self._redis:
            await self._redis.hdel("mcp-hub:api-keys", api_key)


async def get_redis_client() -> RedisClient:
    client = RedisClient()
    await client.connect()
    return client
