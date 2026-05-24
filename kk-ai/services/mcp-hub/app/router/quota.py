"""Quota management API routes."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.quota import (
    ErrorResponse,
    ProjectListResponse,
    QuotaRule,
    QuotaRuleCreate,
    QuotaRuleListResponse,
    QuotaRuleUpdate,
    QuotaUsage,
)
from app.services.quota_service import QuotaService

logger = logging.getLogger("mcp-hub.router.quota")
router = APIRouter(prefix="/api/v1/quota", tags=["quota"])


def _get_quota_service(request: Request) -> QuotaService:
    """Get quota service from app state."""
    return request.app.state.quota_service  # type: ignore[return-value]


@router.get("/rules", response_model=QuotaRuleListResponse)
async def list_rules(
    request: Request,
    project_name: str | None = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List quota rules with pagination."""
    service = _get_quota_service(request)
    items, total = service.list_rules(
        project_name=project_name,
        status=status,
        page=page,
        page_size=page_size,
    )
    return QuotaRuleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/rules", response_model=QuotaRule, status_code=201)
async def create_rule(request: Request, data: QuotaRuleCreate):
    """Create a new quota rule."""
    service = _get_quota_service(request)

    if data.monthly_limit < data.daily_limit:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="VALIDATION_ERROR",
                message="monthly_limit must be greater than or equal to daily_limit",
            ).model_dump(),
        )

    try:
        rule = service.create_rule(data)
        return rule
    except ValueError as exc:
        if str(exc) == "RULE_EXISTS":
            raise HTTPException(
                status_code=409,
                detail=ErrorResponse(
                    error="RULE_EXISTS",
                    message=f"Quota rule for project '{data.project_name}' already exists",
                ).model_dump(),
            )
        raise


@router.get("/rules/{rule_id}", response_model=QuotaRule)
async def get_rule(request: Request, rule_id: str):
    """Get a quota rule by ID."""
    service = _get_quota_service(request)
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="RULE_NOT_FOUND",
                message=f"Rule '{rule_id}' not found",
            ).model_dump(),
        )
    return rule


@router.put("/rules/{rule_id}", response_model=QuotaRule)
async def update_rule(request: Request, rule_id: str, data: QuotaRuleUpdate):
    """Update a quota rule."""
    service = _get_quota_service(request)

    if data.daily_limit is not None and data.monthly_limit is not None:
        if data.monthly_limit < data.daily_limit:
            raise HTTPException(
                status_code=422,
                detail=ErrorResponse(
                    error="VALIDATION_ERROR",
                    message="monthly_limit must be greater than or equal to daily_limit",
                ).model_dump(),
            )

    try:
        rule = service.update_rule(rule_id, data)
        return rule
    except KeyError as exc:
        if str(exc) == "RULE_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="RULE_NOT_FOUND",
                    message=f"Rule '{rule_id}' not found",
                ).model_dump(),
            )
        raise


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(request: Request, rule_id: str):
    """Soft delete a quota rule."""
    service = _get_quota_service(request)
    service.delete_rule(rule_id)
    return None


@router.get("/usage", response_model=list[QuotaUsage])
async def list_usage(request: Request):
    """Get real-time usage for all projects."""
    service = _get_quota_service(request)
    return await service.get_all_usage()


@router.get("/usage/{project_name}", response_model=QuotaUsage)
async def get_project_usage(request: Request, project_name: str):
    """Get real-time usage for a single project."""
    service = _get_quota_service(request)
    return await service.get_usage(project_name)


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(request: Request):
    """List all known project names."""
    service = _get_quota_service(request)
    return ProjectListResponse(items=service.get_projects())
