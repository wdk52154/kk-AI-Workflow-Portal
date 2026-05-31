import httpx
from typing import List, Optional
from app.config import get_settings

async def recall_user_facts(user_id: str) -> List[str]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.MEMORY_SERVICE_URL}/v1/recall_user_facts",
                json={"user_id": user_id},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("facts", [])
    except Exception:
        pass
    return []
