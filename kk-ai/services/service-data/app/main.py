"""Data Service - FastAPI main application entry."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.logger import LoggerMiddleware
from app.router.annotate import router as annotate_router
from app.router.ingest import router as ingest_router
from app.router.products import router as products_router
from app.router.query import router as query_router
from app.router.stats import router as stats_router
from app.services.database import init_db


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-data")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging()

    # Initialize database
    init_db()

    app = FastAPI(
        title="AI Data Center",
        description="ETL Pipeline & Data Products - 统一数据中心",
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

    # Logging middleware
    app.add_middleware(LoggerMiddleware)

    # Register routes
    app.include_router(ingest_router)
    app.include_router(annotate_router)
    app.include_router(query_router)
    app.include_router(products_router)
    app.include_router(stats_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from app.services.data_store import get_data_store

        store = get_data_store()
        stats = store.get_data_stats()

        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "total_records": stats["total_records"],
            "total_cleaned": stats["total_cleaned"],
        }

    return app


app = create_app()
