"""Asset Service - FastAPI main application entry."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.router.assets import router as assets_router


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-asset")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging()
    init_db()

    app = FastAPI(
        title="Asset Management Platform",
        description="素材管理与运营平台",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(assets_router)

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
        }

    return app


app = create_app()
