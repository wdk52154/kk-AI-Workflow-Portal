from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from app.models.voice import (
    ChatRequest, ChatResponse, AudioChatRequest, AudioChatResponse,
    TransferRequest, TransferResponse, SessionHistoryResponse
)
from app.services.voice_store import get_voice_store
from app.services.pipeline import run_pipeline, detect_intent
import json

router = APIRouter(prefix="/v1/voice", tags=["voice"])

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    store = get_voice_store()
    session_id = body.session_id or store.create_session(body.user_id, body.platform)
    result = await run_pipeline(body.message, body.user_id, session_id, body.platform)
    return ChatResponse(**result)

@router.post("/chat/audio")
async def chat_audio(body: AudioChatRequest):
    """语音对话：上传音频 → ASR → Pipeline → TTS"""
    store = get_voice_store()
    session_id = body.session_id or store.create_session(body.user_id)
    # Mock ASR: 假设音频已转写为文字
    mock_text = "我想了解一下你们的产品"
    result = await run_pipeline(mock_text, body.user_id, session_id)
    return AudioChatResponse(
        session_id=session_id,
        text_reply=result["text_reply"],
        audio_url=result.get("audio_url"),
        media_urls=result.get("media_urls", []),
        intent=result["intent"]
    )

@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    store = get_voice_store()
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = store.get_messages(session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        user_id=session["user_id"],
        messages=messages,
        created_at=session["created_at"],
        updated_at=session["updated_at"]
    )

@router.post("/transfer", response_model=TransferResponse)
async def transfer_to_human(body: TransferRequest):
    store = get_voice_store()
    session = store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = store.transfer_session(body.session_id, body.reason)
    messages = store.get_messages(body.session_id)
    context = " | ".join([f"{m['role']}: {m['content'][:50]}" for m in messages[-5:]])
    return TransferResponse(
        session_id=body.session_id,
        status="transferred",
        context_summary=context,
        messages=messages
    )

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    """SSE 流式对话"""
    store = get_voice_store()
    session_id = body.session_id or store.create_session(body.user_id, body.platform)
    result = await run_pipeline(body.message, body.user_id, session_id, body.platform)

    async def event_generator():
        # 发送意图
        yield f"data: {json.dumps({'type': 'intent', 'intent': result['intent']})}\n\n"
        # 发送知识来源
        if result.get('sources'):
            yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
        # 发送文字回复（模拟流式）
        words = result['text_reply']
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        # 发送多媒体
        if result.get('media_urls'):
            yield f"data: {json.dumps({'type': 'media', 'urls': result['media_urls']})}\n\n"
        # 结束
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
