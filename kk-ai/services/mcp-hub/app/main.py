"""MCP HUB Gateway - FastAPI main application entry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.middleware.auth import AuthMiddleware
from app.middleware.logger import LoggerMiddleware, setup_logging
from app.middleware.quota import QuotaMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.router.proxy import router as proxy_router
from app.utils.redis_client import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()

    # Startup
    setup_logging()
    redis_client = RedisClient()
    await redis_client.connect()

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

    # Middleware chain (outer -> inner):
    # Logger -> Quota -> RateLimit -> Auth -> Router
    # Request flow: Auth -> RateLimit -> Quota -> Logger -> handler
    # Response flow: handler -> Logger -> Quota -> RateLimit -> Auth -> client
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(QuotaMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)

    # Register routes
    app.include_router(proxy_router)

    return app


app = create_app()
