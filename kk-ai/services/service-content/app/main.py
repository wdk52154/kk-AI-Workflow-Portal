from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.router.content import router as content_router
from app.services.content_store import get_content_store

def create_app() -> FastAPI:
    settings = get_settings()
    get_content_store()

    app = FastAPI(title="Content Agent", version=settings.VERSION)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(content_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.VERSION}

    return app

app = create_app()
