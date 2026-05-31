from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.content import (
    TopicGenerateRequest, TopicGenerateResponse, TopicItem,
    ContentGenerateRequest, ContentGenerateResponse,
    RewriteRequest, ScheduleRequest, ScheduleItem
)
from app.services.content_store import get_content_store
from app.services.generator import generate_content, generate_topics, rewrite_content
from app.config import get_settings
import httpx

router = APIRouter(prefix="/v1/content", tags=["content"])

@router.post("/topics", response_model=TopicGenerateResponse)
async def generate_topic_list(body: TopicGenerateRequest):
    topics = await generate_topics(body.industry, body.account_positioning, body.count)
    return TopicGenerateResponse(topics=[TopicItem(**t) for t in topics])

@router.post("/generate", response_model=ContentGenerateResponse)
async def generate(body: ContentGenerateRequest):
    store = get_content_store()
    result = await generate_content(
        body.platform, body.topic, body.tone, body.brand,
        body.keywords, body.length
    )
    cid = store.create_content({
        "platform": body.platform,
        "title": result["title"],
        "content": result["content"],
        "tags": result["tags"],
        "tone": body.tone,
        "brand": body.brand,
        "keywords": body.keywords,
        "suggested_images": result["suggested_images"],
    })
    return ContentGenerateResponse(
        id=cid, platform=body.platform, title=result["title"],
        content=result["content"], tags=result["tags"],
        suggested_images=result["suggested_images"],
        created_at=store.get_content(cid)["created_at"]
    )

@router.get("/contents")
async def list_contents(
    platform: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    store = get_content_store()
    return store.list_contents(platform=platform, page=page, page_size=page_size)

@router.get("/contents/{content_id}", response_model=ContentGenerateResponse)
async def get_content(content_id: str):
    store = get_content_store()
    item = store.get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return ContentGenerateResponse(**item)

@router.post("/rewrite", response_model=ContentGenerateResponse)
async def rewrite(body: RewriteRequest):
    store = get_content_store()
    item = store.get_content(body.content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    new_text = rewrite_content(item["content"], body.style, body.tone)
    updated = store.update_content(body.content_id, {"content": new_text})
    return ContentGenerateResponse(**updated)

@router.post("/schedule", response_model=ScheduleItem)
async def schedule(body: ScheduleRequest):
    store = get_content_store()
    sid = store.create_schedule(body.model_dump())
    return ScheduleItem(id=sid, **body.model_dump(), created_at=store.list_schedules()[0]["created_at"] if store.list_schedules() else "")

@router.get("/schedules")
async def list_schedules():
    store = get_content_store()
    return store.list_schedules()

@router.get("/performance")
async def performance():
    store = get_content_store()
    total = store.list_contents(page_size=1)["total"]
    by_platform = {}
    for p in ["xiaohongshu", "wechat", "douyin", "moments"]:
        by_platform[p] = store.list_contents(platform=p, page_size=1)["total"]
    return {
        "total_contents": total,
        "by_platform": by_platform,
        "avg_daily_output": round(total / max(1, 1), 1),
    }
