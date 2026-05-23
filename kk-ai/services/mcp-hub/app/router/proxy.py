"""Dynamic router: forwards requests to downstream services."""

import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import get_settings
from app.models.schemas import HealthStatus
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.router")
router = APIRouter()

# In-memory route cache
_route_cache: dict[str, str] = {}


def _load_routes_from_env() -> None:
    """Load route config from env JSON."""
    global _route_cache
    settings = get_settings()
    if settings.ROUTES_JSON:
        try:
            routes = json.loads(settings.ROUTES_JSON)
            _route_cache = {r["service_name"]: r["target_url"] for r in routes}
            logger.info("Loaded %d routes from env", len(_route_cache))
        except Exception:
            logger.exception("Failed to parse ROUTES_JSON")


_load_routes_from_env()


async def _resolve_target(service_name: str) -> Optional[str]:
    """Resolve service name to target URL."""
    if service_name in _route_cache:
        return _route_cache[service_name]

    # Try Redis
    redis_client = await get_redis_client()
    if redis_client.is_connected:
        target = await redis_client._redis.hget("mcp-hub:routes", service_name)  # type: ignore[union-attr]
        if target:
            _route_cache[service_name] = target
            return target

    return None


@router.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(request: Request, service_name: str, path: str):
    """Proxy request to downstream service."""
    target_base = await _resolve_target(service_name)

    if not target_base:
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.warning("Service not found | service=%s trace_id=%s", service_name, trace_id)
        return JSONResponse(
            status_code=404,
            content={
                "error": "SERVICE_NOT_FOUND",
                "message": f"Service '{service_name}' is not registered",
                "trace_id": trace_id,
            },
        )

    target_url = f"{target_base.rstrip('/')}/{path}"
    query_string = str(request.query_params)
    if query_string:
        target_url = f"{target_url}?{query_string}"

    # Build headers (forward relevant ones, add gateway context)
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in {"host", "content-length", "transfer-encoding"}:
            headers[key] = value

    headers["X-Gateway-Service"] = "mcp-hub"
    headers["X-Trace-Id"] = getattr(request.state, "trace_id", "")
    headers["X-Project-Id"] = getattr(request.state, "project_id", "")

    settings = get_settings()
    method = request.method

    try:
        body = await request.body()
    except Exception:
        body = b""

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        try:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            trace_id = getattr(request.state, "trace_id", "unknown")
            logger.error("Upstream timeout | service=%s url=%s trace_id=%s", service_name, target_url, trace_id)
            return JSONResponse(
                status_code=504,
                content={
                    "error": "GATEWAY_TIMEOUT",
                    "message": "Upstream service timed out",
                    "trace_id": trace_id,
                },
            )
        except httpx.ConnectError as exc:
            trace_id = getattr(request.state, "trace_id", "unknown")
            logger.error("Upstream unreachable | service=%s url=%s trace_id=%s error=%s", service_name, target_url, trace_id, exc)
            return JSONResponse(
                status_code=502,
                content={
                    "error": "BAD_GATEWAY",
                    "message": "Upstream service is unreachable",
                    "trace_id": trace_id,
                },
            )
        except Exception as exc:
            trace_id = getattr(request.state, "trace_id", "unknown")
            logger.exception("Proxy error | service=%s trace_id=%s", service_name, trace_id)
            return JSONResponse(
                status_code=502,
                content={
                    "error": "BAD_GATEWAY",
                    "message": str(exc),
                    "trace_id": trace_id,
                },
            )

    # Stream response back
    content_type = response.headers.get("content-type", "application/octet-stream")

    if "text/event-stream" in content_type:
        return StreamingResponse(
            content=response.aiter_raw(),
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() not in {"content-encoding", "transfer-encoding"}},
            media_type=content_type,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={k: v for k, v in response.headers.items() if k.lower() not in {"content-encoding", "transfer-encoding", "content-length"}},
        media_type=content_type,
    )


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Gateway health check endpoint."""
    redis_client = await get_redis_client()
    redis_ok = redis_client.is_connected

    upstream_status: dict[str, str] = {}
    for svc, url in _route_cache.items():
        upstream_status[svc] = url

    return HealthStatus(
        status="ok" if redis_ok else "degraded",
        redis_connected=redis_ok,
        upstream_services=upstream_status,
    )
