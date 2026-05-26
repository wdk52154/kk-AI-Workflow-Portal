"""RAG Service - FastAPI main application entry."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.project_auth import ProjectAuthMiddleware
from app.router.documents import router as documents_router
from app.router.ingest import router as ingest_router
from app.router.search import router as search_router


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-rag")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging()

    app = FastAPI(
        title="RAG Service",
        description="向量检索与知识库服务，支持文档摄入、语义检索、多租户隔离",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Project ID validation
    app.add_middleware(ProjectAuthMiddleware)

    # Register routes
    app.include_router(ingest_router)
    app.include_router(search_router)
    app.include_router(documents_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from app.services.memory_vector_store import get_vector_store

        vector_store = get_vector_store()
        collections = vector_store.list_collections()

        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "collections_count": len(collections),
            "collections": collections,
        }

    return app


app = create_app()
