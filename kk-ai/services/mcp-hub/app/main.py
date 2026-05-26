"""MCP HUB Gateway - FastAPI main application entry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.auth import AuthMiddleware
from app.middleware.logger import LoggerMiddleware, setup_logging
from app.middleware.quota import QuotaMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.router.admin import router as admin_router
from app.router.proxy import router as proxy_router
from app.router.quota import router as quota_router
from app.services.api_key_service import get_api_key_service
from app.services.quota_service import QuotaService
from app.services.router_service import get_router_service
from app.utils.redis_client import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()

    # Startup
    setup_logging()
    redis_client = RedisClient()
    await redis_client.connect()

    # Connect quota service to Redis
    app.state.quota_service.set_redis_client(redis_client)

    # Sync API keys from Redis
    api_key_service = get_api_key_service()
    await api_key_service.sync_from_redis()

    yield

    # Shutdown
    await redis_client.close()


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="MCP HUB Gateway",
        description="统一 HTTP Gateway，支持 Auth / RateLimit / Quota / Router / Logger 中间件链",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS: allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware chain (outer -> inner):
    # Logger -> Auth -> RateLimit -> Quota -> app
    # Request flow: Auth -> RateLimit -> Quota -> app -> response
    # Logger wraps all to record full lifecycle
    app.add_middleware(QuotaMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggerMiddleware)

    # Initialize services (before lifespan connects Redis)
    app.state.quota_service = QuotaService()

    # Register routes (quota first to avoid proxy catch-all)
    app.include_router(quota_router)
    app.include_router(admin_router)
    app.include_router(proxy_router)

    return app


app = create_app()
