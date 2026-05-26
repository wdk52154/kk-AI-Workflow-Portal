"""Admin API routes for gateway management."""

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import get_settings
from app.models.schemas import GatewayError, HealthStatus, RouteConfig
from app.services.api_key_service import get_api_key_service
from app.services.router_service import get_router_service
from app.utils.redis_client import get_redis_client

logger = logging.getLogger("mcp-hub.router.admin")
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Admin key from env or default
ADMIN_KEY = "kk-admin-key"


def _verify_admin(admin_key: str | None) -> None:
    """Verify admin key."""
    if not admin_key:
        raise HTTPException(
            status_code=401,
            detail=GatewayError(
                error="UNAUTHORIZED",
                message="Missing X-Admin-Key header",
                trace_id="",
            ).model_dump(mode="json"),
        )

    api_key_service = get_api_key_service()
    key_obj = api_key_service.validate(admin_key)
    if not key_obj or key_obj.project_id != "admin":
        raise HTTPException(
            status_code=403,
            detail=GatewayError(
                error="FORBIDDEN",
                message="Invalid admin key",
                trace_id="",
            ).model_dump(mode="json"),
        )


@router.get("/health", response_model=HealthStatus)
async def health_check_admin():
    """Gateway health check (admin version with more details)."""
    redis_client = await get_redis_client()
    redis_ok = redis_client.is_connected

    router_service = get_router_service()
    upstream_status = router_service.get_upstream_status()

    return HealthStatus(
        status="ok" if redis_ok else "degraded",
        redis_connected=redis_ok,
        upstream_services=upstream_status,
    )


@router.get("/routes")
async def list_routes(
    request: Request,
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    """List all active route rules."""
    _verify_admin(x_admin_key)
    router_service = get_router_service()
    routes = router_service.list_routes()
    return {
        "items": [r.to_dict() for r in routes],
        "total": len(routes),
    }


@router.post("/routes", status_code=201)
async def create_route(
    request: Request,
    data: RouteConfig,
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    """Create a new route rule."""
    _verify_admin(x_admin_key)
    router_service = get_router_service()
    rule = router_service.create_route(
        path_prefix=f"/{data.service_name}",
        target_url=data.target_url,
        service_name=data.service_name,
        description=data.description or "",
        timeout_seconds=data.timeout_seconds,
    )
    return rule.to_dict()


@router.delete("/routes/{route_id}", status_code=204)
async def delete_route(
    request: Request,
    route_id: str,
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    """Delete a route rule."""
    _verify_admin(x_admin_key)
    router_service = get_router_service()
    success = router_service.delete_route(route_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=GatewayError(
                error="ROUTE_NOT_FOUND",
                message=f"Route '{route_id}' not found",
                trace_id=getattr(request.state, "trace_id", ""),
            ).model_dump(mode="json"),
        )
    return None


@router.get("/api-keys")
async def list_api_keys(
    request: Request,
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    """List all active API keys."""
    _verify_admin(x_admin_key)
    api_key_service = get_api_key_service()
    keys = api_key_service.list_keys()
    return {
        "items": [
            {
                "key_prefix": k.key[:8] + "...",
                "project_id": k.project_id,
                "name": k.name,
                "rate_limit": k.rate_limit,
                "status": k.status,
            }
            for k in keys
        ],
        "total": len(keys),
    }
