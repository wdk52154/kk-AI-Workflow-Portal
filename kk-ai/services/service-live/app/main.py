from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.router.live import router as live_router
from app.services.live_store import get_live_store
import os

def create_app() -> FastAPI:
    settings = get_settings()
    get_live_store()
    os.makedirs(settings.VIDEO_STORAGE, exist_ok=True)

    app = FastAPI(title="Live Clipping Agent", version=settings.VERSION)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(live_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.VERSION}

    return app

app = create_app()
