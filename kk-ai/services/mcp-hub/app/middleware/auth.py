"""Auth middleware: X-API-Key validation with project isolation."""

import json
import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import get_settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.auth")

# Fallback in-memory store when Redis is unavailable
_in_memory_api_keys: dict[str, dict] = {}


def _load_fallback_keys() -> None:
    """Load API keys from env JSON if Redis is down."""
    global _in_memory_api_keys
    settings = get_settings()
    if settings.API_KEYS_JSON:
        try:
            keys = json.loads(settings.API_KEYS_JSON)
            _in_memory_api_keys = {k["api_key"]: k for k in keys}
            logger.info("Loaded %d fallback API keys from env", len(_in_memory_api_keys))
        except Exception:
            logger.exception("Failed to parse API_KEYS_JSON")


_load_fallback_keys()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Validates X-API-Key header and attaches project info to request.state.
    Skips auth for health endpoints.
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/api/v1/quota"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        settings = get_settings()
        api_key = request.headers.get(settings.API_KEY_HEADER)

        if not api_key:
            logger.warning("Missing API key | trace_id=%s", getattr(request.state, "trace_id", "unknown"))
            return JSONResponse(
                status_code=401,
                content={
                    "error": "UNAUTHORIZED",
                    "message": f"Missing {settings.API_KEY_HEADER} header",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
            )

        project = await self._lookup_project(api_key)

        if not project:
            logger.warning("Invalid API key | trace_id=%s", getattr(request.state, "trace_id", "unknown"))
            return JSONResponse(
                status_code=401,
                content={
                    "error": "UNAUTHORIZED",
                    "message": "Invalid API key",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
            )

        if not project.get("enabled", True):
            logger.warning(
                "Project disabled | project_id=%s trace_id=%s",
                project["project_id"],
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
        request.state.project_id = project["project_id"]
        request.state.project_name = project.get("name", "")
        request.state.daily_quota = project.get("daily_quota", settings.QUOTA_DAILY_DEFAULT)
        request.state.monthly_quota = project.get("monthly_quota", settings.QUOTA_MONTHLY_DEFAULT)
        request.state.rate_limit_per_minute = project.get(
            "rate_limit_per_minute", settings.RATE_LIMIT_DEFAULT_PER_MINUTE
        )

        logger.debug(
            "Auth OK | project_id=%s trace_id=%s",
            project["project_id"],
            getattr(request.state, "trace_id", "unknown"),
        )
        return await call_next(request)

    async def _lookup_project(self, api_key: str) -> Optional[dict]:
        redis_client = await get_redis_client()
        project = await redis_client.get_project_by_api_key(api_key)
        if project:
            return project
        return _in_memory_api_keys.get(api_key)
