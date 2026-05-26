"""Pytest fixtures for service-rag tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.memory_vector_store import get_vector_store


@pytest.fixture
def app():
    """Create a test FastAPI app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_vector_store():
    """Reset vector store state between tests."""
    store = get_vector_store()
    # Clear all collections
    for name in list(store.list_collections()):
        store.delete_collection(name)
    yield


@pytest.fixture
def project_headers():
    """Default project headers."""
    return {"X-Project-Id": "test-project-001"}


@pytest.fixture
def other_project_headers():
    """Different project headers for tenant isolation tests."""
    return {"X-Project-Id": "test-project-002"}
