"""Dynamic router service for downstream service routing."""

import json
import logging
import threading
import uuid
from typing import Optional

from app.config import get_settings

logger = logging.getLogger("mcp-hub.router_service")


class RouteRule:
    """Route rule for forwarding requests to downstream services."""

    def __init__(
        self,
        id: str,
        path_prefix: str,
        target_url: str,
        service_name: str = "",
        description: str = "",
        timeout_seconds: float = 30.0,
        status: str = "active",
    ):
        self.id = id
        self.path_prefix = path_prefix
        self.target_url = target_url.rstrip("/")
        self.service_name = service_name or path_prefix.strip("/").split("/")[0]
        self.description = description
        self.timeout_seconds = timeout_seconds
        self.status = status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path_prefix": self.path_prefix,
            "target_url": self.target_url,
            "service_name": self.service_name,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RouteRule":
        return cls(
            id=data.get("id", ""),
            path_prefix=data.get("path_prefix", ""),
            target_url=data.get("target_url", ""),
            service_name=data.get("service_name", ""),
            description=data.get("description", ""),
            timeout_seconds=data.get("timeout_seconds", 30.0),
            status=data.get("status", "active"),
        )


class RouterService:
    """Dynamic route table management service."""

    def __init__(self):
        self._routes: dict[str, RouteRule] = {}  # id -> RouteRule
        self._prefix_index: list[tuple[str, RouteRule]] = []  # sorted by prefix length desc
        self._lock = threading.Lock()
        self._load_default_routes()

    def _load_default_routes(self) -> None:
        """Load default routes from environment config."""
        settings = get_settings()
        if settings.ROUTES_JSON:
            try:
                routes_data = json.loads(settings.ROUTES_JSON)
                for rd in routes_data:
                    rule = RouteRule(
                        id=str(uuid.uuid4()),
                        path_prefix=f"/{rd['service_name']}",
                        target_url=rd["target_url"],
                        service_name=rd["service_name"],
                    )
                    self._routes[rule.id] = rule
                self._rebuild_index()
                logger.info("Loaded %d routes from env", len(self._routes))
            except Exception:
                logger.exception("Failed to parse ROUTES_JSON")

    def _rebuild_index(self) -> None:
        """Rebuild prefix index for longest-prefix matching."""
        active_routes = [r for r in self._routes.values() if r.status == "active"]
        self._prefix_index = sorted(
            [(r.path_prefix, r) for r in active_routes],
            key=lambda x: len(x[0]),
            reverse=True,
        )

    def create_route(
        self,
        path_prefix: str,
        target_url: str,
        service_name: str = "",
        description: str = "",
        timeout_seconds: float = 30.0,
    ) -> RouteRule:
        """Create a new route rule."""
        with self._lock:
            path_prefix = path_prefix.rstrip("/")
            if not path_prefix.startswith("/"):
                path_prefix = f"/{path_prefix}"

            rule = RouteRule(
                id=str(uuid.uuid4()),
                path_prefix=path_prefix,
                target_url=target_url,
                service_name=service_name or path_prefix.strip("/").split("/")[0],
                description=description,
                timeout_seconds=timeout_seconds,
            )
            self._routes[rule.id] = rule
            self._rebuild_index()
            logger.info("Created route %s -> %s", path_prefix, target_url)
            return rule

    def get_route(self, route_id: str) -> RouteRule | None:
        """Get a route by ID."""
        return self._routes.get(route_id)

    def list_routes(self) -> list[RouteRule]:
        """List all active routes."""
        return [r for r in self._routes.values() if r.status == "active"]

    def delete_route(self, route_id: str) -> bool:
        """Soft delete a route."""
        with self._lock:
            rule = self._routes.get(route_id)
            if not rule:
                return False
            rule.status = "deleted"
            self._rebuild_index()
            logger.info("Deleted route id=%s", route_id)
            return True

    def match(self, path: str) -> RouteRule | None:
        """Match a path to the longest-prefix route rule."""
        for prefix, rule in self._prefix_index:
            if path.startswith(prefix):
                return rule
        return None

    def get_upstream_status(self) -> dict[str, str]:
        """Return upstream service status map."""
        return {r.service_name: r.target_url for r in self.list_routes()}


# Global singleton
_router_service: Optional[RouterService] = None


def get_router_service() -> RouterService:
    """Get or create the global RouterService instance."""
    global _router_service
    if _router_service is None:
        _router_service = RouterService()
    return _router_service
