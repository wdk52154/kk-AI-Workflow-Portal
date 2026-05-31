"""Asset API routes."""

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.models.asset import (
    AssetCreate,
    AssetItem,
    AssetListResponse,
    AssetSearchRequest,
    AssetStatsResponse,
    PosterGenerateRequest,
    PosterGenerateResponse,
)
from app.services.asset_store import get_asset_store
from app.services.storage import get_storage
from app.services.prompt_client import render_poster_template

logger = logging.getLogger("service-asset.router.assets")
router = APIRouter()


@router.post("/v1/assets")
async def upload_asset(
    file: UploadFile = File(...),
    name: str = Form(...),
    asset_type: str = Form(...),
    description: str = Form(default=""),
    tags: str = Form(default=""),
    category: str = Form(default=""),
):
    """Upload a new asset."""
    store = get_asset_store()
    file_data = await file.read()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    asset = store.create_asset(
        name=name,
        asset_type=asset_type,
        file_data=file_data,
        filename=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
        description=description,
        tags=tag_list,
        category=category,
    )

    return asset


@router.get("/v1/assets/search", response_model=AssetListResponse)
async def search_assets(
    q: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Search assets with filters."""
    store = get_asset_store()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    items, total = store.search_assets(
        q=q,
        asset_type=asset_type,
        tags=tag_list,
        category=category,
        status=status,
        page=page,
        page_size=page_size,
    )

    return AssetListResponse(
        items=[AssetItem(**item) for item in items],
        total=total,
    )


@router.get("/v1/assets/stats", response_model=AssetStatsResponse)
async def get_asset_stats():
    """Get asset statistics."""
    store = get_asset_store()
    stats = store.get_stats()
    return AssetStatsResponse(**stats)


@router.get("/v1/assets/{asset_id}")
async def get_asset(asset_id: str):
    """Get asset by ID."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetItem(**asset)


@router.get("/v1/assets/{asset_id}/download")
async def download_asset(asset_id: str):
    """Download asset file."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    storage = get_storage()
    # file_path may be absolute (legacy) or relative key (new storage backend)
    storage_key = asset["file_path"]
    try:
        file_data = storage.read(storage_key)
    except Exception:
        # Fallback: try reading directly from file_path
        try:
            with open(storage_key, "rb") as f:
                file_data = f.read()
        except Exception:
            raise HTTPException(status_code=404, detail="File not found in storage")

    # Record usage
    store.record_usage(asset_id, action="download")

    import urllib.parse
    from fastapi.responses import Response
    ext = os.path.splitext(storage_key)[1]
    safe_filename = urllib.parse.quote(f"{asset['name']}{ext}")
    return Response(
        content=file_data,
        media_type=asset.get("mime_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        },
    )


@router.post("/v1/assets/{asset_id}/status")
async def update_asset_status(asset_id: str, status: str = Form(...)):
    """Update asset status (uploaded/precheck/pending_review/approved/rejected)."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    updated = store.update_status(asset_id, status)
    return AssetItem(**updated)


@router.post("/v1/assets/{asset_id}/precheck")
async def run_precheck(asset_id: str):
    """Run automated content precheck for uploaded asset."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        updated = store.run_precheck(asset_id)
        return AssetItem(**updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/assets/{asset_id}/approve")
async def approve_asset(asset_id: str):
    """Manually approve asset after review."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        updated = store.approve_asset(asset_id)
        return AssetItem(**updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/assets/{asset_id}/reject")
async def reject_asset(asset_id: str):
    """Manually reject asset."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    updated = store.reject_asset(asset_id)
    return AssetItem(**updated)


@router.post("/v1/assets/{asset_id}/generate_poster", response_model=PosterGenerateResponse)
async def generate_poster(asset_id: str, body: PosterGenerateRequest):
    """Generate poster from template."""
    store = get_asset_store()
    asset = store.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset["asset_type"] != "poster_template":
        raise HTTPException(status_code=400, detail="Asset is not a poster template")

    # Call service-prompt:9004 for template rendering
    rendered = await render_poster_template(body.variables)

    if rendered.get("rendered"):
        message = "Poster generated successfully via service-prompt"
    else:
        message = "Poster generated successfully (fallback: service-prompt unavailable)"

    return PosterGenerateResponse(
        asset_id=asset_id,
        download_url=f"/v1/assets/{asset_id}/download",
        message=message,
    )
