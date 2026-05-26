"""Document ingestion API routes."""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.config import get_settings
from app.models.ingest import IngestDocumentResponse
from app.services.document_parser import DocumentParser
from app.services.embedding_client import get_embedding_client
from app.services.memory_vector_store import get_vector_store
from app.services.text_splitter import TokenTextSplitter

logger = logging.getLogger("service-rag.router.ingest")
router = APIRouter()


def _get_project_id(request: Request) -> str:
    return getattr(request.state, "project_id", "")


def _build_where_filter(
    source_type: str | None,
    tags: list[str] | None,
    date_start: str | None,
    date_end: str | None,
) -> dict | None:
    """Build ChromaDB-compatible where filter."""
    where = {}
    if source_type:
        where["source_type"] = source_type
    if tags:
        where["tags"] = {"$in": tags}
    if date_start or date_end:
        date_filter = {}
        if date_start:
            date_filter["$gte"] = date_start
        if date_end:
            date_filter["$lte"] = date_end
        where["created_at"] = date_filter
    return where if where else None


@router.post("/v1/ingest_document", response_model=IngestDocumentResponse)
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    source_type: str = Form("document"),
    tags: str = Form(""),
):
    """Ingest a document: parse, split, embed, store."""
    project_id = _get_project_id(request)
    settings = get_settings()

    # Validate file size
    content = file.file.read()
    file.file.seek(0)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Parse document
    parser = DocumentParser()
    try:
        text = parser.parse(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Split into chunks
    splitter = TokenTextSplitter()
    if file.filename and file.filename.endswith(".md"):
        chunks = splitter.split_markdown(text)
    else:
        chunks = splitter.split(text)

    if len(chunks) > settings.MAX_CHUNKS_PER_DOC:
        raise HTTPException(
            status_code=413,
            detail=f"Too many chunks ({len(chunks)}). Max: {settings.MAX_CHUNKS_PER_DOC}",
        )

    # Get embeddings from LLM Gateway
    embedding_client = get_embedding_client()
    try:
        chunk_texts = [c.text for c in chunks]
        embeddings = await embedding_client.embed(chunk_texts)
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error": "EMBEDDING_FAILED", "message": str(exc)},
        )

    # Store in vector store
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    created_at = datetime.now(timezone.utc).isoformat()

    collection = get_vector_store().get_or_create_collection(f"rag_{project_id}")

    ids = [f"{doc_id}_{c.index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [
        {
            "project_id": project_id,
            "document_id": doc_id,
            "source_type": source_type,
            "filename": file.filename or "unknown",
            "chunk_index": c.index,
            "tags": tag_list,
            "created_at": created_at,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(
        "Ingested document %s for project %s: %d chunks",
        doc_id,
        project_id,
        len(chunks),
    )

    return IngestDocumentResponse(
        document_id=doc_id,
        filename=file.filename or "unknown",
        chunk_count=len(chunks),
    )
