"""Doubao ARK API client."""

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.services.circuit_breaker import CircuitBreaker, RetryWithBackoff, with_circuit_breaker

logger = logging.getLogger("service-llm.ark_client")

# Global circuit breaker for ARK API
circuit_breaker = CircuitBreaker(name="ark_api")
retry_handler = RetryWithBackoff()


class ArkClient:
    """Async client for Doubao ARK OpenAI-compatible API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.ARK_API_KEY
        self.base_url = (base_url or settings.ARK_BASE_URL).rstrip("/")

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Call ARK chat completion API."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        headers = dict(self.client.headers)
        if stream:
            headers["Accept"] = "text/event-stream"

        return await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )

    async def embeddings(
        self,
        model: str,
        input_text: str | list[str],
    ) -> httpx.Response:
        """Call ARK embeddings API."""
        payload = {
            "model": model,
            "input": input_text,
        }
        return await self.client.post(
            f"{self.base_url}/embeddings",
            json=payload,
        )

    async def close(self) -> None:
        await self.client.aclose()


# Wrapped functions with circuit breaker + retry

@with_circuit_breaker(circuit_breaker, retry_handler)
async def chat_completion_with_resilience(
    client: ArkClient,
    model: str,
    messages: list[dict[str, str]],
    stream: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> httpx.Response:
    return await client.chat_completion(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


@with_circuit_breaker(circuit_breaker, retry_handler)
async def embeddings_with_resilience(
    client: ArkClient,
    model: str,
    input_text: str | list[str],
) -> httpx.Response:
    return await client.embeddings(model=model, input_text=input_text)
