"""Pytest fixtures for service-asset tests."""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.database import init_db


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    test_db = "./data/test_assets.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    import app.services.asset_store as store_mod
    import app.database as db_mod

    original_path = db_mod.get_settings().DB_PATH
    db_mod.get_settings().DB_PATH = test_db
    init_db(test_db)

    store_mod._asset_store = None

    yield

    db_mod.get_settings().DB_PATH = original_path
    store_mod._asset_store = None
    if os.path.exists(test_db):
        os.remove(test_db)
