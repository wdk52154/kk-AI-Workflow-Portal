"""Rerank search results using LLM Gateway."""

import json
import logging
import re

import httpx

from app.config import get_settings

logger = logging.getLogger("service-rag.reranker")

RERANK_PROMPT = """You are a relevance ranking assistant.
Given the following query and candidate passages, rank them by relevance to the query.

Query: {query}

Candidates:
{candidates}

Return ONLY a JSON array with objects containing "index" (original candidate index) and "score" (relevance score 0.0-1.0), sorted by score descending (most relevant first):
[{{"index": 0, "score": 0.95}}, {{"index": 2, "score": 0.80}}, ...]"""


class Reranker:
    """Rerank search results using LLM Gateway."""

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.LLM_GATEWAY_URL).rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def rerank(self, query: str, results: list[dict]) -> list[dict]:
        """Rerank results using LLM."""
        if not results:
            return []

        candidates_text = "\n\n".join(
            f"[{i}] {r.get('content', r.get('text', ''))[:400]}"
            for i, r in enumerate(results)
        )
        prompt = RERANK_PROMPT.format(query=query, candidates=candidates_text)

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": None,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            )
            response.raise_for_status()
            data = response.json()

            llm_text = data["choices"][0]["message"]["content"]
            ranked = self._parse_ranking(llm_text, len(results))

            # Reorder results
            reranked_results = []
            for item in ranked:
                idx = item["index"]
                if 0 <= idx < len(results):
                    result = dict(results[idx])
                    result["rerank_score"] = item["score"]
                    reranked_results.append(result)

            # Append any missing results at the end
            seen_indices = {item["index"] for item in ranked}
            for i, result in enumerate(results):
                if i not in seen_indices:
                    result = dict(result)
                    result["rerank_score"] = 0.0
                    reranked_results.append(result)

            return reranked_results

        except Exception as exc:
            logger.warning("Rerank failed, returning original order: %s", exc)
            return results

    def _parse_ranking(self, text: str, num_results: int) -> list[dict]:
        """Parse LLM ranking output."""
        try:
            # Try to extract JSON array
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        # Fallback: return original order
        return [{"index": i, "score": 1.0 - i * 0.1} for i in range(num_results)]

    async def close(self) -> None:
        await self.client.aclose()


# Global singleton
_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Get or create the global Reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
