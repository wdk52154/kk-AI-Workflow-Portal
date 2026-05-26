"""Prompt template manager with YAML hot-reload support."""

import logging
import os
import threading
import time
from typing import Any

import yaml

from app.config import get_settings

logger = logging.getLogger("service-prompt.prompt_manager")


class PromptManager:
    """Manages prompt templates from YAML files with hot-reload."""

    def __init__(self, prompts_dir: str | None = None):
        settings = get_settings()
        self.prompts_dir = prompts_dir or settings.PROMPTS_DIR
        self._prompts: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._last_modified: dict[str, float] = {}
        self._last_check = 0.0
        self._reload_interval = settings.CONFIG_RELOAD_INTERVAL

        os.makedirs(self.prompts_dir, exist_ok=True)
        self._load_all()

    def _load_all(self) -> None:
        """Load all prompt YAML files."""
        if not os.path.exists(self.prompts_dir):
            return

        loaded = 0
        for root, _, files in os.walk(self.prompts_dir):
            for filename in files:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    filepath = os.path.join(root, filename)
                    if self._load_file(filepath):
                        loaded += 1

        logger.info("Loaded %d prompts from %s", loaded, self.prompts_dir)

    def _load_file(self, filepath: str) -> bool:
        """Load a single prompt YAML file. Returns True if successful."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict) or "id" not in data:
                return False

            prompt_id = data["id"]
            with self._lock:
                self._prompts[prompt_id] = data
                self._last_modified[prompt_id] = os.path.getmtime(filepath)

            return True

        except Exception as exc:
            logger.error("Failed to load prompt %s: %s", filepath, exc)
            return False

    def check_reload(self) -> bool:
        """Check for file changes and reload if needed."""
        now = time.time()
        if now - self._last_check < self._reload_interval:
            return False
        self._last_check = now

        changed = False
        if not os.path.exists(self.prompts_dir):
            return False

        for root, _, files in os.walk(self.prompts_dir):
            for filename in files:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    filepath = os.path.join(root, filename)
                    try:
                        mtime = os.path.getmtime(filepath)
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        if data and isinstance(data, dict) and "id" in data:
                            prompt_id = data["id"]
                            last = self._last_modified.get(prompt_id, 0)
                            if mtime > last:
                                if self._load_file(filepath):
                                    logger.info("Hot-reloaded prompt: %s", prompt_id)
                                    changed = True
                    except Exception:
                        pass
        return changed

    def get_prompt(self, prompt_id: str) -> dict[str, Any] | None:
        """Get a prompt by ID."""
        self.check_reload()
        with self._lock:
            return self._prompts.get(prompt_id)

    def list_prompts(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all prompts, optionally filtered by category."""
        self.check_reload()
        with self._lock:
            prompts = list(self._prompts.values())
            if category:
                prompts = [p for p in prompts if p.get("category") == category]
            return prompts

    def register_prompt(self, data: dict[str, Any]) -> str:
        """Register a new prompt and save to YAML file."""
        prompt_id = data.get("id")
        if not prompt_id:
            raise ValueError("Prompt ID is required")

        category = data.get("category", "uncategorized")
        category_dir = os.path.join(self.prompts_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        filepath = os.path.join(category_dir, f"{prompt_id}.yaml")

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        with self._lock:
            self._prompts[prompt_id] = data
            self._last_modified[prompt_id] = os.path.getmtime(filepath)

        logger.info("Registered prompt: %s (category: %s)", prompt_id, category)
        return prompt_id

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        with self._lock:
            if prompt_id not in self._prompts:
                return False
            prompt = self._prompts.pop(prompt_id)
            self._last_modified.pop(prompt_id, None)

        # Try to delete file
        category = prompt.get("category", "uncategorized")
        filepath = os.path.join(self.prompts_dir, category, f"{prompt_id}.yaml")
        if os.path.exists(filepath):
            os.remove(filepath)

        return True


# Global singleton
_prompt_manager: PromptManager | None = None


def get_prompt_manager() -> PromptManager:
    """Get or create the global PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
