"""Quota middleware: Daily / Monthly quota enforcement per project."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.services.quota_service import QuotaService

logger = logging.getLogger("mcp-hub.quota")


class QuotaMiddleware(BaseHTTPMiddleware):
    """Consumes quota per request. Checks daily and monthly limits dynamically."""

    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/quota",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        # Get project name from request state (set by AuthMiddleware) or header
        project_name = getattr(request.state, "project_name", None)
        if not project_name:
            project_name = request.headers.get("X-Project-Name")

        if not project_name:
            return await call_next(request)

        # Get quota service from app state
        quota_service: QuotaService | None = getattr(
            request.app.state, "quota_service", None
        )
        if not quota_service:
            return await call_next(request)

        result = await quota_service.check_and_increment(project_name)

        if not result["allowed"]:
            reason = result["reason"]
            quota_info = result["quota_info"]
            logger.warning(
                "Quota exceeded | project=%s reason=%s daily=%s/%s monthly=%s/%s",
                project_name,
                reason,
                quota_info["daily_used"],
                quota_info["daily_limit"],
                quota_info["monthly_used"],
                quota_info["monthly_limit"],
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "QUOTA_EXCEEDED",
                    "message": f"Quota exceeded: {reason} quota",
                    "type": reason,
                    "quota": quota_info,
                },
            )

        # Log alert if threshold exceeded
        if result.get("alert"):
            quota_info = result["quota_info"]
            logger.warning(
                "QUOTA_ALERT | project=%s usage_rate=%.1f%% threshold=%d%% "
                "daily=%s/%s monthly=%s/%s",
                project_name,
                result.get("usage_rate", 0),
                result.get("alert_threshold", 0),
                quota_info["daily_used"],
                quota_info["daily_limit"],
                quota_info["monthly_used"],
                quota_info["monthly_limit"],
            )

        # Attach quota info for response headers
        request.state.quota_info = result["quota_info"]

        return await call_next(request)
