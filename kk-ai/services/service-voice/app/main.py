from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.router.voice import router as voice_router
from app.services.voice_store import get_voice_store

def create_app() -> FastAPI:
    settings = get_settings()
    store = get_voice_store()

    app = FastAPI(title="AI Voice Agent", version=settings.VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(voice_router)

    @app.get("/health")
    async def health():
        stats = {"total_sessions": 0}
        return {"status": "ok", "version": settings.VERSION, **stats}

    return app

app = create_app()
