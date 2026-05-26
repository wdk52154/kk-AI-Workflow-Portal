"""Embedding API routes."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.embedding import EmbeddingRequest
from app.services.ark_client import ArkClient, embeddings_with_resilience
from app.services.model_manager import get_model_manager

logger = logging.getLogger("service-llm.router.embedding")
router = APIRouter()


@router.post("/v1/embeddings")
async def embeddings(body: EmbeddingRequest):
    """Text embedding endpoint."""
    model_manager = get_model_manager()
    model = model_manager.get_model_for_embedding(body.model)

    if not model:
        available = [m.id for m in model_manager.list_models() if m.supports_embedding]
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MODEL_NOT_FOUND",
                "message": f"Embedding model '{body.model}' not found",
                "available_models": available,
            },
        )

    if not model.supports_embedding:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "EMBEDDING_NOT_SUPPORTED",
                "message": f"Model '{model.id}' does not support embedding",
            },
        )

    client = ArkClient()

    try:
        response = await embeddings_with_resilience(
            client=client,
            model=model.endpoint_id,
            input_text=body.input,
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
        logger.exception("Embedding failed")
        raise HTTPException(
            status_code=504,
            detail={"error": "GATEWAY_TIMEOUT", "message": str(exc)},
        )
    finally:
        await client.close()

    if response.status_code != 200:
        try:
            body_err = response.json()
            error_msg = body_err.get("error", {}).get("message", "Unknown error")
        except Exception:
            error_msg = response.text

        raise HTTPException(
            status_code=502,
            detail={"error": "UPSTREAM_ERROR", "message": error_msg},
        )

    try:
        data = response.json()
        return JSONResponse(content=data)
    except Exception:
        return JSONResponse(content={"raw": response.text})
