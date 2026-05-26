"""User fact API routes for cross-project user profile."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.user_fact import (
    RecallUserFactsRequest,
    RecallUserFactsResponse,
    StoreUserFactRequest,
    StoreUserFactResponse,
    UserFactResult,
)
from app.services.embedding_client import get_embedding_client
from app.services.user_fact_store import get_user_fact_store

logger = logging.getLogger("service-memory.router.user_fact")
router = APIRouter()


@router.post("/v1/store_user_fact", response_model=StoreUserFactResponse)
async def store_user_fact(body: StoreUserFactRequest):
    """Store a user fact (global, cross-project)."""
    embedding_client = get_embedding_client()

    try:
        embedding = await embedding_client.embed_single(body.fact_content)
    except Exception as exc:
        logger.error("Embedding failed for user fact: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
        )

    fact_store = get_user_fact_store()
    fact_id = fact_store.store(
        {
            "user_id": body.user_id,
            "fact_type": body.fact_type,
            "fact_content": body.fact_content,
            "embedding": embedding,
            "confidence": body.confidence,
            "source_project_id": body.source_project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return StoreUserFactResponse(fact_id=fact_id)


@router.post("/v1/recall_user_facts", response_model=RecallUserFactsResponse)
async def recall_user_facts(body: RecallUserFactsRequest):
    """Recall user facts with optional semantic search."""
    query_embedding = None

    if body.query:
        embedding_client = get_embedding_client()
        try:
            query_embedding = await embedding_client.embed_single(body.query)
        except Exception as exc:
            logger.error("Query embedding failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
            )

    fact_store = get_user_fact_store()
    results = fact_store.recall(
        user_id=body.user_id,
        fact_type=body.fact_type,
        query_embedding=query_embedding,
        top_k=body.top_k,
    )

    return RecallUserFactsResponse(
        user_id=body.user_id,
        total=len(results),
        facts=[
            UserFactResult(
                fact_id=r["fact_id"],
                fact_type=r["fact_type"],
                fact_content=r["fact_content"],
                confidence=r["confidence"],
                source_project_id=r["source_project_id"],
                score=r.get("score"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in results
        ],
    )
