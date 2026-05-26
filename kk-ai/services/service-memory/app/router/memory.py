"""Memory API routes for conversation history."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.memory import (
    RecallMemoryRequest,
    RecallMemoryResponse,
    RecallMemoryResult,
    StoreMemoryRequest,
    StoreMemoryResponse,
)
from app.services.embedding_client import get_embedding_client
from app.services.memory_store import get_memory_store

logger = logging.getLogger("service-memory.router.memory")
router = APIRouter()


@router.post("/v1/store_memory", response_model=StoreMemoryResponse)
async def store_memory(body: StoreMemoryRequest):
    """Store a conversation memory with embedding."""
    embedding_client = get_embedding_client()

    try:
        embedding = await embedding_client.embed_single(body.content)
    except Exception as exc:
        logger.error("Embedding failed for memory: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
        )

    memory_store = get_memory_store()
    memory_id = memory_store.store(
        {
            "session_id": body.session_id,
            "user_id": body.user_id,
            "role": body.role,
            "content": body.content,
            "embedding": embedding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    return StoreMemoryResponse(memory_id=memory_id)


@router.post("/v1/recall_memory", response_model=RecallMemoryResponse)
async def recall_memory(body: RecallMemoryRequest):
    """Recall relevant conversation memories."""
    embedding_client = get_embedding_client()

    try:
        query_embedding = await embedding_client.embed_single(body.query)
    except Exception as exc:
        logger.error("Query embedding failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
        )

    memory_store = get_memory_store()
    results = memory_store.recall(
        session_id=body.session_id,
        query_embedding=query_embedding,
        top_k=body.top_k,
    )

    return RecallMemoryResponse(
        query=body.query,
        session_id=body.session_id,
        results=[
            RecallMemoryResult(
                memory_id=r["memory_id"],
                role=r["role"],
                content=r["content"],
                score=r.get("score", 0.0),
                timestamp=r["timestamp"],
            )
            for r in results
        ],
        total=len(results),
    )
