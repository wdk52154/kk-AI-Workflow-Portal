"""Quota business logic service."""

import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.models.quota import (
    QuotaRule,
    QuotaRuleCreate,
    QuotaRuleUpdate,
    QuotaUsage,
)
from app.utils.redis_client import RedisClient

logger = logging.getLogger("mcp-hub.quota_service")


def _get_daily_ttl() -> int:
    """Get seconds until end of day."""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


def _get_monthly_ttl() -> int:
    """Get seconds until end of month."""
    now = datetime.now()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    return int((next_month - now).total_seconds())


def _safe_key(name: str) -> str:
    """Sanitize project name for Redis key."""
    return name.replace("/", "_").replace(":", "_")


class QuotaService:
    """Service for managing quota rules and usage."""

    def __init__(self, redis_client: RedisClient | None = None):
        self._rules: dict[str, QuotaRule] = {}  # id -> rule
        self._project_index: dict[str, str] = {}  # project_name -> rule_id (active only)
        self._lock = threading.Lock()
        self._redis = redis_client
        self._memory_usage: dict[str, int] = {}  # fallback when Redis unavailable

    def set_redis_client(self, redis_client: RedisClient) -> None:
        """Set Redis client (called after connection)."""
        self._redis = redis_client

    # --- Rule CRUD ---

    def create_rule(self, data: QuotaRuleCreate) -> QuotaRule:
        """Create a new quota rule. Raises ValueError if duplicate active rule."""
        with self._lock:
            existing_id = self._project_index.get(data.project_name)
            if existing_id and self._rules[existing_id].status == "active":
                raise ValueError("RULE_EXISTS")

            now = datetime.now(timezone.utc)
            rule = QuotaRule(
                id=str(uuid.uuid4()),
                project_name=data.project_name,
                daily_limit=data.daily_limit,
                monthly_limit=data.monthly_limit,
                alert_threshold=data.alert_threshold,
                status="active",
                created_at=now,
                updated_at=now,
            )
            self._rules[rule.id] = rule
            self._project_index[data.project_name] = rule.id
            return rule

    def get_rule(self, rule_id: str) -> QuotaRule | None:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(
        self,
        project_name: str | None = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[QuotaRule], int]:
        """List rules with filtering and pagination."""
        items = list(self._rules.values())

        if status:
            items = [r for r in items if r.status == status]

        if project_name:
            items = [r for r in items if project_name.lower() in r.project_name.lower()]

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    def update_rule(self, rule_id: str, data: QuotaRuleUpdate) -> QuotaRule:
        """Update a rule. Raises KeyError if not found."""
        with self._lock:
            rule = self._rules.get(rule_id)
            if not rule:
                raise KeyError("RULE_NOT_FOUND")

            update_dict = data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if value is not None:
                    setattr(rule, key, value)

            rule.updated_at = datetime.now(timezone.utc)
            return rule

    def delete_rule(self, rule_id: str) -> None:
        """Soft delete a rule."""
        with self._lock:
            rule = self._rules.get(rule_id)
            if not rule:
                return  # Idempotent

            rule.status = "deleted"
            rule.updated_at = datetime.now(timezone.utc)
            if self._project_index.get(rule.project_name) == rule_id:
                del self._project_index[rule.project_name]

    def get_projects(self) -> list[str]:
        """Get all project names (from active rules + fallback)."""
        projects = set()
        for rule in self._rules.values():
            if rule.status == "active":
                projects.add(rule.project_name)
        projects.update(["project-a", "project-b", "project-c", "kk-ai-platform"])
        return sorted(projects)

    # --- Usage ---

    async def _get_usage_async(self, project_name: str) -> tuple[int, int]:
        """Async get usage from Redis or memory fallback."""
        safe = _safe_key(project_name)
        daily_key = f"quota:daily:{safe}"
        monthly_key = f"quota:monthly:{safe}"

        if not self._redis or not self._redis.is_connected:
            daily = self._memory_usage.get(daily_key, 0)
            monthly = self._memory_usage.get(monthly_key, 0)
            return daily, monthly

        try:
            daily_raw = await self._redis._redis.get(daily_key)  # type: ignore[union-attr]
            monthly_raw = await self._redis._redis.get(monthly_key)  # type: ignore[union-attr]
            daily_used = int(daily_raw or 0)
            monthly_used = int(monthly_raw or 0)
            return daily_used, monthly_used
        except Exception:
            return 0, 0

    async def get_usage(self, project_name: str) -> QuotaUsage:
        """Get real-time usage for a project."""
        rule = None
        for r in self._rules.values():
            if r.project_name == project_name and r.status == "active":
                rule = r
                break

        daily_limit = rule.daily_limit if rule else 0
        monthly_limit = rule.monthly_limit if rule else 0
        alert_threshold = rule.alert_threshold if rule else 80

        daily_used, monthly_used = await self._get_usage_async(project_name)

        daily_rate = (daily_used / daily_limit * 100) if daily_limit > 0 else 0
        monthly_rate = (monthly_used / monthly_limit * 100) if monthly_limit > 0 else 0
        usage_rate = max(daily_rate, monthly_rate)

        if (daily_limit > 0 and daily_used >= daily_limit) or (monthly_limit > 0 and monthly_used >= monthly_limit):
            status: Literal["normal", "warning", "exceeded"] = "exceeded"
        elif usage_rate >= alert_threshold:
            status = "warning"
        else:
            status = "normal"

        return QuotaUsage(
            project_name=project_name,
            daily_used=daily_used,
            daily_limit=daily_limit,
            monthly_used=monthly_used,
            monthly_limit=monthly_limit,
            usage_rate=round(usage_rate, 1),
            status=status,
        )

    async def check_and_increment(
        self,
        project_name: str,
    ) -> dict:
        """
        Check quota and increment counter.
        Returns {"allowed": bool, "reason": str|None, "quota_info": dict, ...}
        """
        rule = None
        for r in self._rules.values():
            if r.project_name == project_name and r.status == "active":
                rule = r
                break

        if not rule:
            return {
                "allowed": True,
                "reason": None,
                "quota_info": {
                    "daily_used": 0,
                    "daily_limit": 0,
                    "monthly_used": 0,
                    "monthly_limit": 0,
                },
            }

        daily_limit = rule.daily_limit
        monthly_limit = rule.monthly_limit
        alert_threshold = rule.alert_threshold

        daily_used, monthly_used = await self._get_usage_async(project_name)

        if daily_used >= daily_limit:
            return {
                "allowed": False,
                "reason": "daily",
                "quota_info": {
                    "daily_used": daily_used,
                    "daily_limit": daily_limit,
                    "monthly_used": monthly_used,
                    "monthly_limit": monthly_limit,
                },
            }

        if monthly_used >= monthly_limit:
            return {
                "allowed": False,
                "reason": "monthly",
                "quota_info": {
                    "daily_used": daily_used,
                    "daily_limit": daily_limit,
                    "monthly_used": monthly_used,
                    "monthly_limit": monthly_limit,
                },
            }

        # Increment
        safe = _safe_key(project_name)
        daily_key = f"quota:daily:{safe}"
        monthly_key = f"quota:monthly:{safe}"

        if self._redis and self._redis.is_connected:
            try:
                pipe = self._redis._redis.pipeline()  # type: ignore[union-attr]
                pipe.incr(daily_key)
                pipe.incr(monthly_key)
                pipe.expire(daily_key, _get_daily_ttl())
                pipe.expire(monthly_key, _get_monthly_ttl())
                await pipe.execute()
            except Exception:
                pass
        else:
            self._memory_usage[daily_key] = self._memory_usage.get(daily_key, 0) + 1
            self._memory_usage[monthly_key] = self._memory_usage.get(monthly_key, 0) + 1

        new_daily = daily_used + 1
        new_monthly = monthly_used + 1
        daily_rate = (new_daily / daily_limit * 100) if daily_limit > 0 else 0
        monthly_rate = (new_monthly / monthly_limit * 100) if monthly_limit > 0 else 0
        usage_rate = max(daily_rate, monthly_rate)

        return {
            "allowed": True,
            "reason": None,
            "quota_info": {
                "daily_used": new_daily,
                "daily_limit": daily_limit,
                "monthly_used": new_monthly,
                "monthly_limit": monthly_limit,
            },
            "alert": usage_rate >= alert_threshold,
            "usage_rate": usage_rate,
            "alert_threshold": alert_threshold,
        }

    async def get_all_usage(self) -> list[QuotaUsage]:
        """Get usage for all projects with active rules."""
        results: list[QuotaUsage] = []
        for rule in self._rules.values():
            if rule.status == "active":
                try:
                    usage = await self.get_usage(rule.project_name)
                    results.append(usage)
                except Exception:
                    pass
        return results
