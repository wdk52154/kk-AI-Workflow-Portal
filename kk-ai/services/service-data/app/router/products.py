"""Data products router (sales scripts, objections, user profiles)."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.models import (
    ObjectionItem,
    ObjectionsResponse,
    SalesScriptItem,
    SalesScriptsResponse,
    UserProfileItem,
    UserProfilesResponse,
)
from app.services.data_store import get_data_store
from app.services.memory_client import get_memory_client

logger = logging.getLogger("service-data.router.products")
router = APIRouter()


def _parse_tags(tags: str | None) -> list[str] | None:
    """Parse tags query parameter."""
    if not tags:
        return None
    try:
        return json.loads(tags)
    except Exception:
        return [t.strip() for t in tags.split(",") if t.strip()]


@router.get("/v1/products/sales_scripts", response_model=SalesScriptsResponse)
async def get_sales_scripts(
    project_id: str | None = None,
    min_conversion_rate: float = Query(default=0.0, ge=0.0, le=1.0),
    tags: str | None = None,
):
    """Get Top Sales scripts - high-conversion sales dialogues."""
    settings = get_settings()
    store = get_data_store()
    tag_list = _parse_tags(tags)

    # Query cleaned data with intent=高转化 and quality >= threshold
    rows, total = store.query_cleaned(
        project_id=project_id,
        intent="高转化",
        min_quality_score=settings.QUALITY_THRESHOLD,
        page=1,
        page_size=100,
    )

    scripts = []
    for idx, row in enumerate(rows):
        row_tags = []
        if row.get("tags"):
            try:
                row_tags = json.loads(row["tags"])
            except Exception:
                row_tags = []

        # Filter by tags if specified
        if tag_list and not any(t in row_tags for t in tag_list):
            continue

        # Mock conversion rate based on quality score
        conversion_rate = min(0.99, (row.get("quality_score", 50) or 50) / 100.0)
        if conversion_rate < min_conversion_rate:
            continue

        scripts.append(
            SalesScriptItem(
                script_id=f"script_{row['id']}",
                content=row["cleaned_content"],
                conversion_rate=round(conversion_rate, 2),
                usage_count=(row.get("quality_score") or 50) * 2,
                tags=row_tags,
                source_project_id=row["project_id"],
                created_at=row["created_at"],
            )
        )

    return SalesScriptsResponse(scripts=scripts, total=len(scripts))


@router.get("/v1/products/objections", response_model=ObjectionsResponse)
async def get_objections(
    project_id: str | None = None,
    objection_type: str | None = None,
    tags: str | None = None,
):
    """Get customer objections and standard responses."""
    settings = get_settings()
    store = get_data_store()
    tag_list = _parse_tags(tags)

    rows, total = store.query_cleaned(
        project_id=project_id,
        intent="客户异议",
        min_quality_score=settings.QUALITY_THRESHOLD,
        page=1,
        page_size=100,
    )

    objections = []
    for row in rows:
        row_tags = []
        if row.get("tags"):
            try:
                row_tags = json.loads(row["tags"])
            except Exception:
                row_tags = []

        if tag_list and not any(t in row_tags for t in tag_list):
            continue

        if objection_type and objection_type not in row_tags:
            continue

        # Parse objection/response from content
        content = row["cleaned_content"]
        parts = content.split("\n", 1)
        objection_text = parts[0] if parts else content
        response_text = parts[1] if len(parts) > 1 else "暂无标准应答"

        objections.append(
            ObjectionItem(
                objection_id=f"obj_{row['id']}",
                objection_text=objection_text,
                response_text=response_text,
                objection_type=objection_type or "general",
                frequency=(row.get("quality_score") or 50) * 5,
                tags=row_tags,
                source_project_id=row["project_id"],
                created_at=row["created_at"],
            )
        )

    return ObjectionsResponse(objections=objections, total=len(objections))


@router.get("/v1/products/user_profiles", response_model=UserProfilesResponse)
async def get_user_profiles(
    user_id: str | None = None,
    project_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Get structured user profiles from memory service."""
    if user_id:
        # Fetch single user profile
        memory_client = get_memory_client()
        try:
            result = await memory_client.recall_user_facts(user_id)
            facts = result.get("facts", [])

            # Build profile from facts
            preferences = []
            constraints = []
            for fact in facts:
                fact_type = fact.get("fact_type", "")
                content = fact.get("content", "")
                if fact_type == "preference":
                    preferences.append(content)
                elif fact_type == "constraint":
                    constraints.append(content)

            profile = UserProfileItem(
                user_id=user_id,
                basic={},
                preferences=preferences,
                constraints=constraints,
                value_score=50,
                interaction_count=len(facts),
                last_interaction=facts[0].get("updated_at") if facts else None,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            return UserProfilesResponse(profiles=[profile], total=1)
        except Exception as exc:
            logger.error("Failed to fetch user profile for %s: %s", user_id, exc)
            raise HTTPException(
                status_code=502,
                detail={"error": "MEMORY_SERVICE_ERROR", "message": str(exc)},
            )

    # If no user_id specified, return empty (memory service doesn't support list all)
    return UserProfilesResponse(profiles=[], total=0)
