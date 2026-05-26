"""Document management API routes."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.document import DocumentChunksResponse, DocumentInfo, DocumentListResponse, ChunkInfo
from app.services.memory_vector_store import get_vector_store

logger = logging.getLogger("service-rag.router.documents")
router = APIRouter()


def _get_project_id(request: Request) -> str:
    return getattr(request.state, "project_id", "")


@router.get("/v1/documents", response_model=DocumentListResponse)
async def list_documents(request: Request):
    """List all documents for the project."""
    project_id = _get_project_id(request)
    collection = get_vector_store().get_or_create_collection(f"rag_{project_id}")

    results = collection.get()

    # Group by document_id
    docs: dict[str, dict] = {}
    for id_, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
        doc_id = meta.get("document_id", "unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "document_id": doc_id,
                "filename": meta.get("filename", "unknown"),
                "source_type": meta.get("source_type", "document"),
                "tags": meta.get("tags", []),
                "created_at": meta.get("created_at"),
                "chunk_count": 0,
            }
        docs[doc_id]["chunk_count"] += 1

    documents = [
        DocumentInfo(
            document_id=d["document_id"],
            filename=d["filename"],
            source_type=d["source_type"],
            chunk_count=d["chunk_count"],
            tags=d["tags"],
            created_at=d["created_at"],
        )
        for d in docs.values()
    ]

    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/v1/documents/{document_id}", status_code=204)
async def delete_document(request: Request, document_id: str):
    """Delete a document and all its chunks."""
    project_id = _get_project_id(request)
    collection = get_vector_store().get_or_create_collection(f"rag_{project_id}")

    # Find all chunks for this document
    results = collection.get()
    chunk_ids_to_delete = [
        id_ for id_, meta in zip(results["ids"], results["metadatas"])
        if meta.get("document_id") == document_id
    ]

    if not chunk_ids_to_delete:
        raise HTTPException(
            status_code=404,
            detail={"error": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found"},
        )

    collection.delete(ids=chunk_ids_to_delete)
    logger.info("Deleted document %s with %d chunks", document_id, len(chunk_ids_to_delete))
    return None


@router.get("/v1/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(request: Request, document_id: str):
    """Get all chunks for a document."""
    project_id = _get_project_id(request)
    collection = get_vector_store().get_or_create_collection(f"rag_{project_id}")

    results = collection.get()
    chunks = []
    for id_, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
        if meta.get("document_id") == document_id:
            chunks.append(
                ChunkInfo(
                    chunk_id=id_,
                    chunk_index=meta.get("chunk_index", 0),
                    text=doc,
                    metadata=meta,
                )
            )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail={"error": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found"},
        )

    chunks.sort(key=lambda c: c.chunk_index)
    return DocumentChunksResponse(document_id=document_id, chunks=chunks, total=len(chunks))
