"""LLM Gateway - FastAPI main application entry."""

import json
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.router.chat import router as chat_router
from app.router.embedding import router as embedding_router
from app.router.models import router as models_router
from app.services.circuit_breaker import get_circuit_breaker


def setup_logging() -> None:
    """Configure structured JSON logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger("service-llm")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging()

    app = FastAPI(
        title="LLM Gateway",
        description="豆包 ARK LLM 能力网关，支持 Chat Completion / Embedding / 模型管理",
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
    app.include_router(chat_router)
    app.include_router(embedding_router)
    app.include_router(models_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from app.services.model_manager import get_model_manager

        model_manager = get_model_manager()
        models = model_manager.list_models()
        chat_models = [m.id for m in models if m.supports_streaming]
        embedding_models = [m.id for m in models if m.supports_embedding]

        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "models_loaded": len(models),
            "chat_models": chat_models,
            "embedding_models": embedding_models,
            "circuit_breaker": get_circuit_breaker().get_status(),
        }

    return app


app = create_app()
