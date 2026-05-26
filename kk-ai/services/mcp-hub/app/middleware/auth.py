"""Auth middleware: X-API-Key validation with project isolation via APIKeyService."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings
from app.services.api_key_service import get_api_key_service

logger = logging.getLogger("mcp-hub.auth")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Validates X-API-Key header and attaches project info to request.state.
    Uses APIKeyService for multi-project key management.
    Skips auth for exempt paths.
    """

    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/quota",
        "/api/v1/admin",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        settings = get_settings()
        api_key = request.headers.get(settings.API_KEY_HEADER)

        if not api_key:
            logger.warning(
                "Missing API key | trace_id=%s",
                getattr(request.state, "trace_id", "unknown"),
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "UNAUTHORIZED",
                    "message": f"Missing {settings.API_KEY_HEADER} header",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
            )

        api_key_service = get_api_key_service()
        key_obj = api_key_service.validate(api_key)

        if not key_obj:
            logger.warning(
                "Invalid API key | trace_id=%s",
                getattr(request.state, "trace_id", "unknown"),
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "UNAUTHORIZED",
                    "message": "Invalid API key",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
            )

        if key_obj.status != "active":
            logger.warning(
                "Project disabled | project_id=%s trace_id=%s",
                key_obj.project_id,
                getattr(request.state, "trace_id", "unknown"),
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "FORBIDDEN",
                    "message": "Project is disabled",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
            )

        # Attach project info to request state
        request.state.project_id = key_obj.project_id
        request.state.project_name = key_obj.name
        request.state.daily_quota = key_obj.daily_quota
        request.state.monthly_quota = key_obj.monthly_quota
        request.state.rate_limit_per_minute = key_obj.rate_limit

        logger.debug(
            "Auth OK | project_id=%s trace_id=%s",
            key_obj.project_id,
            getattr(request.state, "trace_id", "unknown"),
        )
        return await call_next(request)
