import httpx
from typing import Optional, List
from app.config import get_settings

async def get_prompt_template(prompt_id: str) -> Optional[dict]:
    """从 service-prompt:9004 获取 Prompt 模板"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.PROMPT_SERVICE_URL}/v1/prompts/{prompt_id}",
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None

async def render_prompt(prompt_id: str, variables: dict) -> Optional[str]:
    """渲染 Prompt 模板"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.PROMPT_SERVICE_URL}/v1/prompts/{prompt_id}/render",
                json={"variables": variables},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("rendered")
    except Exception:
        pass
    return None
