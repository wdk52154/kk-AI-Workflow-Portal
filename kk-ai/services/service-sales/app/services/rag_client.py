import httpx
from typing import List, Optional
from app.config import get_settings

async def search_scripts(query: str, scenario: Optional[str] = None, top_k: int = 5) -> List[dict]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.RAG_SERVICE_URL}/v1/search",
                json={"query": query, "top_k": top_k},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                return results
    except Exception:
        pass
    return []

async def ingest_script(script_id: str, title: str, content: str, category: str, tags: List[str]):
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.RAG_SERVICE_URL}/v1/documents/ingest",
                json={
                    "document_id": f"script-{script_id}",
                    "content": f"{title}\n{content}",
                    "metadata": {"category": category, "tags": tags, "type": "sales_script"}
                },
                timeout=10.0
            )
    except Exception:
        pass
