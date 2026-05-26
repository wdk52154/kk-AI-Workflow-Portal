"""Chat Completion API routes."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.chat import ChatCompletionRequest, ChatCompletionResponse
from app.services.ark_client import ArkClient, chat_completion_with_resilience
from app.services.model_manager import get_model_manager

logger = logging.getLogger("service-llm.router.chat")
router = APIRouter()


def _handle_ark_error(response) -> None:
    """Handle ARK API error responses."""
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = {"error": {"message": response.text}}

    error_msg = body.get("error", {}).get("message", "Unknown error")

    if status == 429:
        raise HTTPException(
            status_code=429,
            detail={"error": "RATE_LIMITED", "message": error_msg},
            headers={"Retry-After": "60"},
        )
    elif status in (500, 502, 503):
        raise HTTPException(
            status_code=502,
            detail={"error": "UPSTREAM_ERROR", "message": error_msg},
        )
    elif status in (401, 403):
        raise HTTPException(
            status_code=status,
            detail={"error": "AUTH_ERROR", "message": error_msg},
        )
    else:
        raise HTTPException(
            status_code=502,
            detail={"error": "UPSTREAM_ERROR", "message": error_msg},
        )


@router.post("/v1/chat/completions")
async def chat_completion(request: Request, body: ChatCompletionRequest):
    """Chat completion endpoint (streaming and non-streaming)."""
    model_manager = get_model_manager()
    model = model_manager.get_model_for_chat(body.model)

    if not model:
        available = [m.id for m in model_manager.list_models()]
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MODEL_NOT_FOUND",
                "message": f"Model '{body.model}' not found",
                "available_models": available,
            },
        )

    if not model.supports_streaming and body.stream:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "STREAMING_NOT_SUPPORTED",
                "message": f"Model '{model.id}' does not support streaming",
            },
        )

    client = ArkClient()

    try:
        response = await chat_completion_with_resilience(
            client=client,
            model=model.endpoint_id,
            messages=[m.model_dump() for m in body.messages],
            stream=body.stream,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            top_p=body.top_p,
        )
    except Exception as exc:
        if "Circuit breaker" in str(exc):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "CIRCUIT_OPEN",
                    "message": "LLM service temporarily unavailable",
                },
            )
        logger.exception("Chat completion failed")
        raise HTTPException(
            status_code=504,
            detail={"error": "GATEWAY_TIMEOUT", "message": str(exc)},
        )
    finally:
        await client.close()

    if response.status_code != 200:
        _handle_ark_error(response)

    if body.stream:
        async def event_stream():
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield f"{line}\n\n"
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping stream")
                    break
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # Non-streaming
    try:
        data = response.json()
        return JSONResponse(content=data)
    except Exception:
        return JSONResponse(content={"raw": response.text})
