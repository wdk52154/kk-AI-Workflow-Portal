"""Client for Memory Service (service-memory:9003)."""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("service-data.memory_client")

_memory_client: "MemoryClient | None" = None


class MemoryClient:
    """HTTP client for interacting with Memory Service."""

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.MEMORY_SERVICE_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def recall_user_facts(self, user_id: str, top_k: int = 10) -> dict:
        """Recall user facts from memory service."""
        payload = {
            "user_id": user_id,
            "query": user_id,
            "top_k": top_k,
        }
        response = await self.client.post("/v1/recall_user_facts", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


def get_memory_client() -> MemoryClient:
    """Get singleton MemoryClient instance."""
    global _memory_client
    if _memory_client is None:
        _memory_client = MemoryClient()
    return _memory_client
