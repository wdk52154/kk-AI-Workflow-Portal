"""Client for service-prompt:9004."""

import httpx

from app.config import get_settings


async def render_poster_template(variables: dict[str, str]) -> dict:
    """Render poster template via service-prompt:9004."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.PROMPT_SERVICE_URL}/v1/prompts/asset_description_enhance/render",
                json={"variables": variables},
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "rendered": data.get("rendered", ""),
                    "variables_used": data.get("variables_used", []),
                }
    except Exception:
        pass
    return {"rendered": "", "variables_used": []}
