"""Prompt Center - FastAPI main application entry."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.router.mcp import router as mcp_router
from app.router.prompts import router as prompts_router


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-prompt")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging()

    app = FastAPI(
        title="Prompt Center",
        description="MCP 原生 Prompt 模板引擎，支持 YAML 配置、Jinja2 渲染、热更新",
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
    app.include_router(prompts_router)
    app.include_router(mcp_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from app.services.prompt_manager import get_prompt_manager

        manager = get_prompt_manager()
        prompts = manager.list_prompts()

        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "prompts_loaded": len(prompts),
            "categories": list({p.get("category", "uncategorized") for p in prompts}),
        }

    return app


app = create_app()
