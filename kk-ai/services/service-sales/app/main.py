from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.router.sales import router as sales_router
from app.services.script_store import get_script_store

def create_app() -> FastAPI:
    settings = get_settings()
    store = get_script_store()
    store._init_db()

    app = FastAPI(title="Sales Intelligence Agent", version=settings.VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(sales_router)

    @app.get("/health")
    async def health():
        stats = store.list_scripts(page_size=1)
        return {
            "status": "ok",
            "version": settings.VERSION,
            "total_scripts": stats["total"]
        }

    return app

app = create_app()
