"""AI Voice Agent 7阶段 Pipeline（LangGraph 编排）"""

import httpx
from typing import Optional, List, Literal
from app.config import get_settings

INTENT_TYPES = ["consult", "complaint", "order", "chat", "transfer"]

async def detect_intent(message: str) -> str:
    """阶段1: 意图识别"""
    msg = message.lower()
    if "转人工" in msg or "人工" in msg or "客服" in msg:
        return "transfer"
    if any(w in msg for w in ["买", "下单", "购买", "多少钱", "价格"]):
        return "order"
    if any(w in msg for w in ["投诉", "不好", "差", "退货", "退款"]):
        return "complaint"
    if any(w in msg for w in ["怎么", "如何", "是什么", "介绍"]):
        return "consult"
    return "chat"

async def retrieve_knowledge(query: str, top_k: int = 3) -> List[dict]:
    """阶段2: 知识检索 - 调用 service-rag:9002"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.RAG_SERVICE_URL}/v1/search",
                json={"query": query, "top_k": top_k},
                timeout=8.0
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
    except Exception:
        pass
    return []

async def recall_user_memory(user_id: str) -> List[str]:
    """阶段3: 记忆召回 - 调用 service-memory:9003"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.MEMORY_SERVICE_URL}/v1/recall_user_facts",
                json={"user_id": user_id, "top_k": 5},
                timeout=8.0
            )
            if resp.status_code == 200:
                facts = resp.json().get("facts", [])
                return [f["fact_content"] for f in facts]
    except Exception:
        pass
    return []

async def generate_response(
    message: str,
    intent: str,
    knowledge: List[dict],
    user_facts: List[str],
    history: List[dict]
) -> str:
    """阶段4: 话术生成 - 调用 service-llm:9001"""
    settings = get_settings()

    # 构建 context
    context_parts = [f"用户意图: {intent}"]
    if knowledge:
        context_parts.append("相关知识:\n" + "\n".join([k.get("content", "") for k in knowledge[:3]]))
    if user_facts:
        context_parts.append("用户画像:\n" + "\n".join(user_facts))

    context = "\n\n".join(context_parts)
    history_text = "\n".join([f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in history[-6:]])

    prompt = f"""你是一位专业的 AI 客服。请根据以下信息回复用户。

{context}

对话历史:
{history_text}

用户最新消息: {message}

请给出专业、友好、简洁的回复（不超过 200 字）:"""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.MCP_HUB_URL}/v1/chat/completions",
                headers={"X-API-Key": settings.API_KEY, "Content-Type": "application/json"},
                json={"model": "doubao-pro", "messages": [{"role": "user", "content": prompt}],
                "stream": False},
                timeout=15.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    # Fallback 话术
    fallbacks = {
        "transfer": "好的，正在为您转接人工客服，请稍等...",
        "order": "感谢您的关注！我们的产品价格实惠，现在下单还有优惠哦。",
        "complaint": "非常抱歉给您带来不好的体验，我们会尽快为您处理。",
        "consult": "好的，我来为您详细介绍。我们的产品采用最新技术，质量有保障。",
        "chat": "您好！有什么我可以帮您的吗？",
    }
    return fallbacks.get(intent, "您好，请问有什么可以帮您？")

async def match_media(intent: str, query: str) -> List[str]:
    """阶段5: 多模态组装 - 调用 service-asset:9006"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ASSET_SERVICE_URL}/v1/assets/search",
                params={"q": query, "asset_type": "image", "status": "approved"},
                timeout=5.0
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                return [f"{settings.ASSET_SERVICE_URL}/v1/assets/{i['asset_id']}/download"
                        for i in items[:2]]
    except Exception:
        pass
    return []

async def ingest_conversation(
    session_id: str, user_id: str, messages: List[dict]
) -> bool:
    """阶段7: 数据沉淀 - 回写 service-data:9005"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/v1/data/ingest",
                json={
                    "data_id": f"voice-{session_id}",
                    "content": json.dumps(messages),
                    "metadata": {"user_id": user_id, "source": "service-voice"},
                    "data_type": "conversation"
                },
                timeout=8.0
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False

async def run_pipeline(
    message: str, user_id: str, session_id: str, platform: str = "web"
) -> dict:
    """执行完整的 7 阶段 Pipeline"""
    import json
    from app.services.voice_store import get_voice_store

    store = get_voice_store()
    session = store.get_session(session_id)
    if not session:
        session_id = store.create_session(user_id, platform)

    history = store.get_messages(session_id)

    # Stage 1: 意图识别
    intent = await detect_intent(message)

    # Stage 2: 知识检索
    knowledge = await retrieve_knowledge(message)

    # Stage 3: 记忆召回
    user_facts = await recall_user_memory(user_id)

    # Stage 4: 话术生成
    reply = await generate_response(message, intent, knowledge, user_facts, history)

    # Stage 5: 多模态组装
    media_urls = []
    if intent == "order" or intent == "consult":
        media_urls = await match_media(intent, message)

    # Stage 6: TTS（mock，返回空 URL）
    audio_url = None

    # 存储消息
    store.add_message(session_id, "user", message, intent)
    store.add_message(session_id, "assistant", reply, intent, media_urls)

    # Stage 7: 数据沉淀（异步，不阻塞响应）
    import asyncio
    asyncio.create_task(ingest_conversation(
        session_id, user_id, store.get_messages(session_id)
    ))

    return {
        "session_id": session_id,
        "text_reply": reply,
        "audio_url": audio_url,
        "media_urls": media_urls,
        "intent": intent,
        "sources": [k.get("document_id", "") for k in knowledge]
    }
