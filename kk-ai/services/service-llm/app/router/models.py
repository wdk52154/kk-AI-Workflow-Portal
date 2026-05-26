"""Model list API routes."""

from fastapi import APIRouter

from app.models.models import ModelInfo, ModelListResponse
from app.services.model_manager import get_model_manager

router = APIRouter()


@router.get("/v1/models")
async def list_models():
    """List available models."""
    model_manager = get_model_manager()
    models = model_manager.list_models()

    return ModelListResponse(
        data=[
            ModelInfo(
                id=m.id,
                object="model",
                created=0,
                owned_by=m.provider,
            )
            for m in models
        ]
    )
