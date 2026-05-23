"""Quota middleware: Daily / Monthly quota enforcement per project."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.quota")


class QuotaMiddleware(BaseHTTPMiddleware):
    """
    Consumes quota per request. Checks daily and monthly limits.
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        project_id = getattr(request.state, "project_id", None)
        if not project_id:
            return await call_next(request)

        settings = get_settings()
        daily_quota = getattr(request.state, "daily_quota", settings.QUOTA_DAILY_DEFAULT)
        monthly_quota = getattr(request.state, "monthly_quota", settings.QUOTA_MONTHLY_DEFAULT)

        redis_client = await get_redis_client()
        allowed, quota_info = await redis_client.check_and_consume_quota(
            project_id=project_id,
            daily_quota=daily_quota,
            monthly_quota=monthly_quota,
        )

        if not allowed:
            reason = quota_info.get("reason", "quota_exceeded")
            logger.warning(
                "Quota exceeded | project_id=%s reason=%s daily=%s/%s monthly=%s/%s trace_id=%s",
                project_id,
                reason,
                quota_info["daily_used"],
                quota_info["daily_limit"],
                quota_info["monthly_used"],
                quota_info["monthly_limit"],
                getattr(request.state, "trace_id", "unknown"),
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "QUOTA_EXCEEDED",
                    "message": f"Quota exceeded: {reason}",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                    "quota": quota_info,
                },
            )

        # Attach quota info for response headers
        request.state.quota_info = quota_info

        logger.debug(
            "Quota OK | project_id=%s daily=%s/%s monthly=%s/%s trace_id=%s",
            project_id,
            quota_info["daily_used"],
            quota_info["daily_limit"],
            quota_info["monthly_used"],
            quota_info["monthly_limit"],
            getattr(request.state, "trace_id", "unknown"),
        )
        return await call_next(request)
