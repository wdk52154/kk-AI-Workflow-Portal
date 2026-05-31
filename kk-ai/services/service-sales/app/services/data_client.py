import httpx
from typing import List, Optional
from app.config import get_settings

async def ingest_conversation(
    conversation_id: str,
    content: str,
    metadata: dict,
    source: str = "sales_agent"
) -> bool:
    """将对话数据回流到 service-data:9005 数据中心"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/v1/data/ingest",
                json={
                    "data_id": f"conv-{conversation_id}",
                    "content": content,
                    "metadata": {
                        **metadata,
                        "source": source,
                        "service": "service-sales",
                    },
                    "data_type": "conversation",
                },
                timeout=10.0,
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False

async def ingest_script_to_data(script_id: str, title: str, content: str,
                                 category: str, tags: List[str]) -> bool:
    """将新录入的话术回流到数据中心"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/v1/data/ingest",
                json={
                    "data_id": f"script-{script_id}",
                    "content": f"{title}\n{content}",
                    "metadata": {
                        "category": category,
                        "tags": tags,
                        "type": "sales_script",
                        "source": "service-sales",
                    },
                    "data_type": "sales_script",
                },
                timeout=10.0,
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False
