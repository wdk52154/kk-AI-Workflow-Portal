"""Knowledge search API routes."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.models.search import SearchKnowledgeRequest, SearchKnowledgeResponse, SearchResultItem
from app.services.embedding_client import get_embedding_client
from app.services.memory_vector_store import get_vector_store
from app.services.reranker import get_reranker

logger = logging.getLogger("service-rag.router.search")
router = APIRouter()


def _get_project_id(request: Request) -> str:
    return getattr(request.state, "project_id", "")


def _build_chroma_where(filters: dict | None) -> dict | None:
    """Build ChromaDB where filter from request filters."""
    if not filters:
        return None

    where = {}
    if "source_type" in filters:
        where["source_type"] = filters["source_type"]
    if "tags" in filters:
        where["tags"] = {"$in": filters["tags"]}
    if "date_range" in filters:
        dr = filters["date_range"]
        date_filter = {}
        if "start" in dr:
            date_filter["$gte"] = dr["start"]
        if "end" in dr:
            date_filter["$lte"] = dr["end"]
        if date_filter:
            where["created_at"] = date_filter

    return where if where else None


@router.post("/v1/search_knowledge", response_model=SearchKnowledgeResponse)
async def search_knowledge(request: Request, body: SearchKnowledgeRequest):
    """Search knowledge base with vector similarity."""
    project_id = _get_project_id(request)
    settings = get_settings()

    top_k = min(body.top_k, settings.MAX_TOP_K)

    # Get query embedding
    embedding_client = get_embedding_client()
    try:
        query_embedding = await embedding_client.embed_single(body.query)
    except Exception as exc:
        logger.error("Query embedding failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
        )

    # Search vector store
    collection = get_vector_store().get_or_create_collection(f"rag_{project_id}")
    where_filter = _build_chroma_where(body.filters)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )
    except Exception as exc:
        logger.error("Vector search failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "SEARCH_FAILED", "message": str(exc)},
        )

    # Format results
    search_results = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc_id, text, meta, dist in zip(ids, documents, metadatas, distances):
        score = max(0.0, 1.0 - float(dist))
        search_results.append({
            "content": text,
            "score": round(score, 4),
            "metadata": meta or {},
        })

    # Optional rerank
    reranked = False
    if body.rerank and search_results:
        reranker = get_reranker()
        try:
            search_results = await reranker.rerank(body.query, search_results)
            reranked = True
        except Exception as exc:
            logger.warning("Rerank failed: %s", exc)

    return SearchKnowledgeResponse(
        query=body.query,
        results=[SearchResultItem(**r) for r in search_results],
        total=len(search_results),
        reranked=reranked,
    )
