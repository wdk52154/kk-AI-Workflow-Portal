"""Model configuration manager with YAML hot-reload support."""

import logging
import os
import threading
import time
from typing import Any

import yaml

from app.config import get_settings

logger = logging.getLogger("service-llm.model_manager")


class ModelConfig:
    """Single model configuration."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data["id"]
        self.name: str = data.get("name", self.id)
        self.provider: str = data.get("provider", "doubao")
        self.endpoint_id: str = data.get("endpoint_id", "")
        self.context_length: int = data.get("context_length", 4096)
        self.temperature_range: list[float] = data.get("temperature_range", [0.0, 1.0])
        self.max_tokens: int = data.get("max_tokens", 4096)
        self.pricing: dict[str, float] = data.get("pricing", {})
        self.supports_streaming: bool = data.get("supports_streaming", True)
        self.supports_embedding: bool = data.get("supports_embedding", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "supports_streaming": self.supports_streaming,
            "supports_embedding": self.supports_embedding,
        }


class ModelManager:
    """Manages model configurations from YAML with hot-reload."""

    def __init__(self, config_path: str | None = None):
        settings = get_settings()
        self.config_path = config_path or settings.MODELS_CONFIG_PATH
        self._models: dict[str, ModelConfig] = {}
        self._default_chat_model: str = ""
        self._default_embedding_model: str = ""
        self._lock = threading.RLock()
        self._last_modified: float = 0.0
        self._last_check: float = 0.0
        self._reload_interval = settings.CONFIG_RELOAD_INTERVAL

        self._load()

    def _load(self) -> bool:
        """Load models from YAML file. Returns True if successful."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning("Model config not found: %s", self.config_path)
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "models" not in data:
                logger.warning("Invalid model config format")
                return False

            with self._lock:
                self._models = {}
                for m in data["models"]:
                    model = ModelConfig(m)
                    self._models[model.id] = model

                self._default_chat_model = data.get("default_chat_model", "")
                self._default_embedding_model = data.get("default_embedding_model", "")
                self._last_modified = os.path.getmtime(self.config_path)

            logger.info("Loaded %d models from %s", len(self._models), self.config_path)
            return True

        except Exception:
            logger.exception("Failed to load model config from %s", self.config_path)
            return False

    def check_reload(self) -> bool:
        """Check if config file has changed and reload if needed."""
        now = time.time()
        if now - self._last_check < self._reload_interval:
            return False

        self._last_check = now

        try:
            if not os.path.exists(self.config_path):
                return False

            mtime = os.path.getmtime(self.config_path)
            if mtime > self._last_modified:
                logger.info("Model config changed, reloading...")
                return self._load()
        except Exception:
            logger.exception("Error checking config file")

        return False

    def get_model(self, model_id: str | None) -> ModelConfig | None:
        """Get model config by ID. Returns None if not found."""
        self.check_reload()
        with self._lock:
            return self._models.get(model_id)

    def list_models(self) -> list[ModelConfig]:
        """List all available models."""
        self.check_reload()
        with self._lock:
            return list(self._models.values())

    def get_default_chat_model(self) -> str:
        """Get default chat model ID."""
        return self._default_chat_model

    def get_default_embedding_model(self) -> str:
        """Get default embedding model ID."""
        return self._default_embedding_model

    def get_model_for_chat(self, model_id: str | None) -> ModelConfig | None:
        """Get model for chat completion. Falls back to default only if model_id is None."""
        if model_id:
            return self.get_model(model_id)
        if self._default_chat_model:
            return self.get_model(self._default_chat_model)
        return None

    def get_model_for_embedding(self, model_id: str | None) -> ModelConfig | None:
        """Get model for embedding. Falls back to default only if model_id is None."""
        if model_id:
            return self.get_model(model_id)
        if self._default_embedding_model:
            return self.get_model(self._default_embedding_model)
        return None


# Global singleton
_model_manager: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """Get or create the global ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
