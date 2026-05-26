"""Jinja2-based template rendering engine with sandboxing."""

import logging
from typing import Any

from jinja2 import Environment, UndefinedError, meta
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger("service-prompt.template_engine")


class TemplateEngine:
    """Jinja2-based template rendering engine with sandbox security."""

    def __init__(self):
        # Use SandboxedEnvironment to prevent SSTI attacks
        self.env = SandboxedEnvironment()

    def render(self, template_text: str, variables: dict[str, Any]) -> str:
        """Render a template with variables."""
        template = self.env.from_string(template_text)
        return template.render(**variables)

    def get_variables(self, template_text: str) -> set[str]:
        """Extract variable names from template."""
        ast = self.env.parse(template_text)
        return meta.find_undeclared_variables(ast)

    def validate(self, prompt_data: dict[str, Any], variables: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate that all required variables are provided."""
        template = prompt_data.get("template", "")
        if not template:
            return True, []

        declared_vars = self.get_variables(template)

        # Get required variables from prompt definition
        prompt_vars = prompt_data.get("variables", [])
        required_names = {
            v["name"] for v in prompt_vars
            if isinstance(v, dict) and v.get("required", False)
        }

        # Also consider any undeclared variable in template as potentially required
        missing = [v for v in required_names if v not in variables]

        return len(missing) == 0, missing

    def apply_defaults(self, prompt_data: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
        """Apply default values for optional variables."""
        result = dict(variables)
        prompt_vars = prompt_data.get("variables", [])
        for var_def in prompt_vars:
            if isinstance(var_def, dict):
                name = var_def.get("name")
                if name and name not in result and "default" in var_def:
                    result[name] = var_def["default"]
        return result
