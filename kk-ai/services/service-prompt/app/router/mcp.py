"""MCP-compatible prompt API routes."""

from fastapi import APIRouter, HTTPException

from app.models.prompt import MCPPromptArgument, MCPPromptDetail
from app.services.prompt_manager import get_prompt_manager

router = APIRouter()


@router.get("/mcp/prompts")
async def mcp_list_prompts():
    """MCP-compatible prompt list."""
    manager = get_prompt_manager()
    prompts = manager.list_prompts()

    return {
        "prompts": [
            {
                "name": p["id"],
                "description": p.get("description", ""),
            }
            for p in prompts
        ]
    }


@router.get("/mcp/prompts/{prompt_id}")
async def mcp_get_prompt(prompt_id: str):
    """MCP-compatible prompt detail."""
    manager = get_prompt_manager()
    prompt = manager.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "message": f"Prompt '{prompt_id}' not found"},
        )

    variables = prompt.get("variables", [])
    arguments = [
        MCPPromptArgument(
            name=v.get("name", ""),
            description=v.get("description"),
            required=v.get("required", False),
        )
        for v in variables
        if isinstance(v, dict)
    ]

    return MCPPromptDetail(
        name=prompt["id"],
        description=prompt.get("description"),
        arguments=arguments,
    )
