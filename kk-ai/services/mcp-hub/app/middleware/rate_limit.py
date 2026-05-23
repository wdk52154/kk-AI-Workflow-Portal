"""Rate Limit middleware: Redis sliding window per project + endpoint."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limit based on Redis sorted sets.
    Key format: ratelimit:{project_id}:{endpoint}
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

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
        limit = getattr(request.state, "rate_limit_per_minute", settings.RATE_LIMIT_DEFAULT_PER_MINUTE)

        redis_client = await get_redis_client()
        allowed, current, limit = await redis_client.check_rate_limit(
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
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {current}/{limit} per minute",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                    "quota": {"current": current, "limit": limit, "window": "1 minute"},
                },
            )

        logger.debug(
            "Rate limit OK | project_id=%s endpoint=%s current=%s/%s trace_id=%s",
            project_id,
            endpoint,
            current,
            limit,
            getattr(request.state, "trace_id", "unknown"),
        )
        return await call_next(request)
