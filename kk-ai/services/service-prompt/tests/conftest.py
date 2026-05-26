"""Pytest fixtures for service-prompt tests."""

import os
import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.prompt_manager import get_prompt_manager


@pytest.fixture
def app():
    """Create a test FastAPI app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_prompts():
    """Reset prompt manager and clean test prompts between tests."""
    import app.services.prompt_manager as pm_mod

    test_dir = "./prompts_test"
    original_dir = pm_mod.get_settings().PROMPTS_DIR

    # Use test prompts directory
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

    pm_mod.get_settings().PROMPTS_DIR = test_dir
    pm_mod._prompt_manager = None

    yield

    # Cleanup
    pm_mod.get_settings().PROMPTS_DIR = original_dir
    pm_mod._prompt_manager = None
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
