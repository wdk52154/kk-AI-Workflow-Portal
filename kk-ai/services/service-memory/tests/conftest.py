"""Pytest fixtures for service-memory tests."""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.database import init_db


@pytest.fixture
def app():
    """Create a test FastAPI app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database between tests."""
    test_db = "./data/test_memory.db"
    # Remove test db if exists
    if os.path.exists(test_db):
        os.remove(test_db)
    # Use test db
    import app.services.database as db_mod
    import app.services.memory_store as mem_mod
    import app.services.user_fact_store as fact_mod

    original_path = db_mod.get_settings().DB_PATH
    db_mod.get_settings().DB_PATH = test_db
    init_db(test_db)

    # Reset singletons
    mem_mod._memory_store = None
    fact_mod._user_fact_store = None

    yield

    # Cleanup
    db_mod.get_settings().DB_PATH = original_path
    mem_mod._memory_store = None
    fact_mod._user_fact_store = None
    if os.path.exists(test_db):
        os.remove(test_db)
