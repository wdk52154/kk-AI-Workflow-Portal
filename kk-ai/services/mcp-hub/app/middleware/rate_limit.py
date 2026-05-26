"""Rate Limit middleware: Redis sliding window per project + endpoint with memory fallback."""

import asyncio
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.rate_limit")

# Memory fallback for rate limiting when Redis is unavailable
_memory_counters: dict[str, list[float]] = {}
_memory_lock = asyncio.Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limit based on Redis sorted sets.
    Falls back to memory-mode counters when Redis is unavailable.
    Key format: ratelimit:{project_id}:{endpoint}
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/api/v1/admin"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        project_id = getattr(request.state, "project_id", None)
        if not project_id:
            # Auth middleware should run before this; if not, skip
            return await call_next(request)

        settings = get_settings()
        endpoint = path.split("/")[1] if len(path.split("/")) > 1 else "default"
        limit = getattr(
            request.state, "rate_limit_per_minute", settings.RATE_LIMIT_DEFAULT_PER_MINUTE
        )

        allowed, current, retry_after = await self._check_rate_limit(
            project_id=project_id,
            endpoint=endpoint,
            limit=limit,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded | project_id=%s endpoint=%s current=%s limit=%s trace_id=%s",
                project_id,
                endpoint,
                current,
                limit,
                getattr(request.state, "trace_id", "unknown"),
            )
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {current}/{limit} per minute",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                    "quota": {"current": current, "limit": limit, "window": "1 minute"},
                },
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        logger.debug(
            "Rate limit OK | project_id=%s endpoint=%s current=%s/%s trace_id=%s",
            project_id,
            endpoint,
            current,
            limit,
            getattr(request.state, "trace_id", "unknown"),
        )
        return await call_next(request)

    async def _check_rate_limit(
        self,
        project_id: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check rate limit. Returns (allowed, current_count, retry_after_seconds).
        """
        redis_client = await get_redis_client()

        if redis_client.is_connected:
            # Redis mode: sliding window with sorted sets
            try:
                now = time.time()
                key = f"ratelimit:{project_id}:{endpoint}"
                window_start = now - window_seconds

                pipe = redis_client._redis.pipeline()  # type: ignore[union-attr]
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window_seconds + 1)
                results = await pipe.execute()

                current_count = results[1] + 1
                allowed = current_count <= limit

                if not allowed:
                    # Rollback the added entry if over limit
                    await redis_client._redis.zrem(key, str(now))  # type: ignore[union-attr]
                    current_count -= 1
                    retry_after = window_seconds - int(now % window_seconds)
                    return False, current_count, retry_after

                return True, current_count, 0
            except Exception:
                # Redis error, fallback to memory
                pass

        # Memory fallback mode
        return await self._check_memory_rate_limit(
            project_id, endpoint, limit, window_seconds
        )

    async def _check_memory_rate_limit(
        self,
        project_id: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """Memory-based sliding window rate limit."""
        global _memory_counters
        key = f"{project_id}:{endpoint}"
        now = time.time()
        window_start = now - window_seconds

        async with _memory_lock:
            timestamps = _memory_counters.get(key, [])
            # Remove expired entries
            timestamps = [t for t in timestamps if t > window_start]
            current_count = len(timestamps) + 1

            if current_count > limit:
                retry_after = window_seconds - int(now % window_seconds)
                return False, current_count - 1, retry_after

            timestamps.append(now)
            _memory_counters[key] = timestamps
            return True, current_count, 0
