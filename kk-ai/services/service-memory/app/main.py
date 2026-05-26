"""Memory Service - FastAPI main application entry."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.router.memory import router as memory_router
from app.router.user_fact import router as user_fact_router
from app.services.database import init_db


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-memory")
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
        title="Memory Service",
        description="对话记忆与用户画像服务，支持跨项目用户事实共享",
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

    # Register routes
    app.include_router(memory_router)
    app.include_router(user_fact_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from app.services.memory_store import get_memory_store
        from app.services.user_fact_store import get_user_fact_store

        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "hot_memories": len(get_memory_store()._hot),
        }

    return app


app = create_app()
