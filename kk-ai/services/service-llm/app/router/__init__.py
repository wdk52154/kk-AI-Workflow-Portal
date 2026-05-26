"""Router package."""

from app.router.chat import router as chat_router
from app.router.embedding import router as embedding_router
from app.router.models import router as models_router

__all__ = ["chat_router", "embedding_router", "models_router"]
