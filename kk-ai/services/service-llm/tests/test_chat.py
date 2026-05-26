"""Tests for chat completion API."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient


def test_chat_model_not_found(client: TestClient) -> None:
    """Test chat with non-existent model returns 404."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "non-existent-model",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "MODEL_NOT_FOUND"


def test_chat_missing_messages(client: TestClient) -> None:
    """Test chat without messages returns validation error."""
    response = client.post(
        "/v1/chat/completions",
        json={"model": "doubao-lite-4k"},
    )
    assert response.status_code == 422


def test_chat_non_streaming_mock(client: TestClient) -> None:
    """Test non-streaming chat with mocked ARK response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "chat-test-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "doubao-lite-4k",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    }

    async_mock = AsyncMock()
    async_mock.__aenter__ = AsyncMock(return_value=mock_response)
    async_mock.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.ark_client.ArkClient.chat_completion", return_value=mock_response):
        with patch("app.services.ark_client.ArkClient.close", new_callable=AsyncMock):
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "doubao-lite-4k",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": False,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["choices"][0]["message"]["content"] == "Hello!"


def test_chat_streaming_mock(client: TestClient) -> None:
    """Test streaming chat with mocked SSE events."""
    async def mock_aiter_lines():
        yield "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}"
        yield "data: {\"choices\":[{\"delta\":{\"content\":\"!\"}}]}"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines

    with patch("app.services.ark_client.ArkClient.chat_completion", return_value=mock_response):
        with patch("app.services.ark_client.ArkClient.close", new_callable=AsyncMock):
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "doubao-lite-4k",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": True,
                },
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            content = response.content.decode("utf-8")
            assert "data:" in content
            assert "[DONE]" in content


def test_chat_streaming_not_supported(client: TestClient) -> None:
    """Test streaming with non-streaming model returns 400."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "doubao-embedding",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "STREAMING_NOT_SUPPORTED"
