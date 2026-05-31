from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.sales import (
    ScriptCreate, ScriptResponse, SalesQueryRequest, SalesQueryResponse,
    RoleplayStartRequest, RoleplayStartResponse, RoleplayChatRequest,
    RoleplayChatResponse, RoleplayEvaluateRequest, RoleplayEvaluateResponse
)
from app.models.conversation import ConversationResponse
from app.services.script_store import get_script_store
from app.services.rag_client import search_scripts, ingest_script
from app.services.memory_client import recall_user_facts
from app.services.roleplay import create_session, chat, evaluate
from app.services.data_client import ingest_script_to_data, ingest_conversation
from app.config import get_settings

router = APIRouter(prefix="/v1/sales", tags=["sales"])

# ---- Scripts CRUD ----
@router.post("/scripts", response_model=ScriptResponse, status_code=201)
async def create_script(body: ScriptCreate):
    store = get_script_store()
    sid = store.create_script(body.model_dump())
    # 回流到 RAG 知识库
    await ingest_script(sid, body.title, body.content, body.category, body.tags)
    # 回流到数据中心 service-data:9005
    await ingest_script_to_data(sid, body.title, body.content, body.category, body.tags)
    return store.get_script(sid)

@router.get("/scripts")
async def list_scripts(
    category: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    store = get_script_store()
    return store.list_scripts(category=category, q=q, page=page, page_size=page_size)

@router.get("/scripts/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: str):
    store = get_script_store()
    script = store.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.delete("/scripts/{script_id}", status_code=204)
async def delete_script(script_id: str):
    store = get_script_store()
    if not store.delete_script(script_id):
        raise HTTPException(status_code=404, detail="Script not found")
    return None

# ---- Sales Query ----
@router.post("/query", response_model=SalesQueryResponse)
async def sales_query(body: SalesQueryRequest):
    store = get_script_store()

    # 1. 召回用户画像
    user_facts = []
    if body.user_id:
        user_facts = await recall_user_facts(body.user_id)

    # 2. RAG 检索话术
    rag_results = await search_scripts(body.customer_question, body.scenario)

    # 3. 本地库检索
    local_results = store.list_scripts(q=body.customer_question, page_size=5)
    local_items = local_results.get("data", [])

    # 合并去重
    seen = set()
    recommended = []
    for item in rag_results + local_items:
        sid = item.get("id") or item.get("document_id", "").replace("script-", "")
        if sid and sid not in seen:
            seen.add(sid)
            script = store.get_script(sid)
            if script:
                recommended.append(ScriptResponse(**script))
                store.increment_usage(sid)

    # 从用户事实中提取禁忌关键词（如过敏源、不喜欢的产品等）
    forbidden_keywords = []
    for fact in user_facts:
        fact_lower = fact.lower()
        if "过敏" in fact_lower:
            # 提取过敏源："用户对芒果过敏" → "芒果"
            import re
            match = re.search(r'对(\w+)过敏', fact)
            if match:
                forbidden_keywords.append(match.group(1))
        if "不喜欢" in fact_lower or "讨厌" in fact_lower:
            import re
            match = re.search(r'不喜欢(\w+)|讨厌(\w+)', fact)
            if match:
                kw = match.group(1) or match.group(2)
                if kw:
                    forbidden_keywords.append(kw)

    # 过滤包含禁忌关键词的推荐话术
    filtered_recommended = []
    for script in recommended:
        content_lower = script.content.lower()
        if not any(kw in content_lower for kw in forbidden_keywords):
            filtered_recommended.append(script)

    # 异议处理建议
    objection_handler = None
    if forbidden_keywords:
        objection_handler = f"注意：客户画像显示「{'; '.join(user_facts)}」，已自动规避含 {'/'.join(forbidden_keywords)} 的相关推荐。"
    else:
        for fact in user_facts:
            if "过敏" in fact or "不喜欢" in fact:
                objection_handler = f"注意：客户画像显示「{fact}」，推荐时自动规避相关产品。"
                break

    return SalesQueryResponse(
        recommended_scripts=filtered_recommended[:5],
        objection_handler=objection_handler,
        user_facts=user_facts,
        confidence=min(0.7 + len(filtered_recommended) * 0.05, 0.95)
    )

# ---- Roleplay ----
@router.post("/roleplay/start", response_model=RoleplayStartResponse)
async def roleplay_start(body: RoleplayStartRequest):
    result = create_session(body.customer_type, body.scenario, body.product)
    return RoleplayStartResponse(**result)

@router.post("/roleplay/chat", response_model=RoleplayChatResponse)
async def roleplay_chat(body: RoleplayChatRequest):
    result = chat(body.session_id, body.message)
    return RoleplayChatResponse(**result)

@router.post("/roleplay/evaluate", response_model=RoleplayEvaluateResponse)
async def roleplay_evaluate(body: RoleplayEvaluateRequest):
    result = evaluate(body.session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    # 评估后自动回流优质对话到数据中心（评分≥80）
    if result["total_score"] >= 80:
        await ingest_conversation(
            body.session_id,
            content="\n".join([f"{m['role']}: {m['content']}" for m in result["transcript"]]),
            metadata={
                "session_id": body.session_id,
                "total_score": result["total_score"],
                "dimensions": result["dimensions"],
                "customer_type": result.get("customer_type", "unknown"),
                "quality": "high",
            }
        )

    return RoleplayEvaluateResponse(
        total_score=result["total_score"],
        dimensions=result["dimensions"],
        suggestions=result["suggestions"],
        transcript=result["transcript"]
    )

# ---- Conversations ----
@router.get("/conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    store = get_script_store()
    return store.list_sessions(page=page, page_size=page_size)
