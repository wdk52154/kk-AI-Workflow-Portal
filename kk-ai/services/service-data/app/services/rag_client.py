"""Client for RAG Service (service-rag:9002)."""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("service-data.rag_client")

_rag_client: "RAGClient | None" = None


class RAGClient:
    """HTTP client for interacting with RAG Service."""

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.RAG_SERVICE_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def ingest_document(
        self, content: str, metadata: dict | None = None, doc_id: str | None = None
    ) -> dict:
        """Ingest a document into RAG for vectorization."""
        payload = {
            "content": content,
            "metadata": metadata or {},
        }
        if doc_id:
            payload["doc_id"] = doc_id

        response = await self.client.post("/v1/ingest_document", json=payload)
        response.raise_for_status()
        return response.json()

    async def search_knowledge(
        self, query: str, top_k: int = 5, project_id: str | None = None
    ) -> dict:
        """Search knowledge in RAG."""
        payload = {
            "query": query,
            "top_k": top_k,
        }
        if project_id:
            payload["metadata_filter"] = {"project_id": project_id}

        response = await self.client.post("/v1/search_knowledge", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


def get_rag_client() -> RAGClient:
    """Get singleton RAGClient instance."""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client
