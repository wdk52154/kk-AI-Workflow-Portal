"""Client for LLM Gateway Embedding API."""

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("service-rag.embedding_client")


class EmbeddingClient:
    """Async client for LLM Gateway Embedding API."""

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.LLM_GATEWAY_URL).rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts."""
        if not texts:
            return []

        payload: dict[str, Any] = {"input": texts}
        if model:
            payload["model"] = model

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            embeddings = [item["embedding"] for item in data["data"]]
            logger.debug("Got %d embeddings from LLM Gateway", len(embeddings))
            return embeddings

        except httpx.HTTPStatusError as exc:
            logger.error("Embedding API error: %s - %s", exc.response.status_code, exc.response.text)
            raise
        except Exception as exc:
            logger.error("Embedding request failed: %s", exc)
            raise

    async def embed_single(self, text: str, model: str | None = None) -> list[float]:
        """Get embedding for a single text."""
        embeddings = await self.embed([text], model=model)
        return embeddings[0]

    async def close(self) -> None:
        await self.client.aclose()


# Global singleton
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    """Get or create the global EmbeddingClient instance."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client
