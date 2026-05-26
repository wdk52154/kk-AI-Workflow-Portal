"""Pytest fixtures for service-data tests."""

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
    test_db = "./data/test_data.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    import app.services.data_store as ds_mod
    import app.services.database as db_mod

    original_path = db_mod.get_settings().DB_PATH
    db_mod.get_settings().DB_PATH = test_db
    init_db(test_db)

    # Reset singletons
    ds_mod._data_store = None

    yield

    # Cleanup
    db_mod.get_settings().DB_PATH = original_path
    ds_mod._data_store = None
    if os.path.exists(test_db):
        os.remove(test_db)
