"""Prompt API routes."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.prompt import (
    PromptListItem,
    PromptListResponse,
    RegisterPromptRequest,
    RegisterPromptResponse,
    RenderPromptRequest,
    RenderPromptResponse,
)
from app.services.prompt_manager import get_prompt_manager
from app.services.template_engine import TemplateEngine

logger = logging.getLogger("service-prompt.router.prompts")
router = APIRouter()

template_engine = TemplateEngine()


@router.get("/v1/prompts", response_model=PromptListResponse)
async def list_prompts(category: str | None = Query(None)):
    """List all prompts, optionally filtered by category."""
    manager = get_prompt_manager()
    prompts = manager.list_prompts(category=category)

    return PromptListResponse(
        items=[
            PromptListItem(
                prompt_id=p["id"],
                name=p.get("name", p["id"]),
                category=p.get("category", "uncategorized"),
                version=p.get("version", "1.0.0"),
                description=p.get("description"),
            )
            for p in prompts
        ],
        total=len(prompts),
    )


@router.get("/v1/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get a prompt template by ID."""
    manager = get_prompt_manager()
    prompt = manager.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "message": f"Prompt '{prompt_id}' not found"},
        )

    return prompt


@router.post("/v1/prompts/{prompt_id}/render", response_model=RenderPromptResponse)
async def render_prompt(prompt_id: str, body: RenderPromptRequest):
    """Render a prompt with variables."""
    manager = get_prompt_manager()
    prompt = manager.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "message": f"Prompt '{prompt_id}' not found"},
        )

    # Validate required variables
    valid, missing = template_engine.validate(prompt, body.variables)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail={"error": "MISSING_VARIABLES", "missing": missing},
        )

    # Apply defaults
    vars_with_defaults = template_engine.apply_defaults(prompt, body.variables)

    # Render template
    template_text = prompt.get("template", "")
    try:
        rendered = template_engine.render(template_text, vars_with_defaults)
    except Exception as exc:
        logger.error("Template render failed for %s: %s", prompt_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "RENDER_FAILED", "message": str(exc)},
        )

    declared_vars = list(template_engine.get_variables(template_text))

    return RenderPromptResponse(
        prompt_id=prompt_id,
        rendered=rendered,
        variables_used=declared_vars,
        variables_missing=[],
    )


@router.post("/v1/prompts", response_model=RegisterPromptResponse)
async def register_prompt(body: RegisterPromptRequest):
    """Register a new prompt."""
    manager = get_prompt_manager()

    try:
        manager.register_prompt(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to register prompt: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "REGISTER_FAILED", "message": str(exc)},
        )

    return RegisterPromptResponse(
        prompt_id=body.id,
        version="1.0.0",
    )


@router.delete("/v1/prompts/{prompt_id}", status_code=204)
async def delete_prompt(prompt_id: str):
    """Delete a prompt."""
    manager = get_prompt_manager()
    success = manager.delete_prompt(prompt_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "message": f"Prompt '{prompt_id}' not found"},
        )

    return None
