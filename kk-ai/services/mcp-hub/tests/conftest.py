"""Pytest fixtures for mcp-hub tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.utils.redis_client import RedisClient


@pytest.fixture
def app():
    """Create a test FastAPI app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def redis_client():
    """Create a test Redis client."""
    client = RedisClient()
    await client.connect()
    yield client
    await client.close()


@pytest.fixture(autouse=True)
def reset_redis_mock(monkeypatch):
    """Reset Redis mock state between tests."""
    # In test environment without Redis, client falls back to memory mode
    pass
