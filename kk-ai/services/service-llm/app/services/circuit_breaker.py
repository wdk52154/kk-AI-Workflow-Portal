"""Circuit breaker with retry mechanism for downstream API calls."""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

from app.config import get_settings

logger = logging.getLogger("service-llm.circuit_breaker")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        self.message = message
        super().__init__(self.message)


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
    ):
        settings = get_settings()
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or settings.CIRCUIT_RECOVERY_TIMEOUT
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def _on_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker '%s' closed", self.name)

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker '%s' opened after %d failures",
                self.name,
                self.failure_count,
            )

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker '%s' half-open", self.name)
                return True
            return False
        return True  # HALF_OPEN

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not self.can_execute():
            raise CircuitOpenError(
                f"LLM service temporarily unavailable (circuit '{self.name}' is open)"
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
        }


# Global default circuit breaker
_default_circuit_breaker = CircuitBreaker(name="default")


def get_circuit_breaker() -> CircuitBreaker:
    """Get the default circuit breaker instance."""
    return _default_circuit_breaker


class RetryWithBackoff:
    """Retry decorator with exponential backoff."""

    def __init__(
        self,
        max_attempts: int | None = None,
        base_delay: float | None = None,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        settings = get_settings()
        self.max_attempts = max_attempts or settings.RETRY_MAX_ATTEMPTS
        self.base_delay = base_delay or settings.RETRY_BASE_DELAY
        self.exceptions = exceptions

    async def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        last_exception: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.exceptions as exc:
                last_exception = exc
                if attempt < self.max_attempts:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Attempt %d/%d failed for %s, retrying in %.1fs: %s",
                        attempt,
                        self.max_attempts,
                        func.__name__,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "All %d attempts failed for %s",
                        self.max_attempts,
                        func.__name__,
                    )

        raise last_exception or Exception("All retry attempts failed")


def with_circuit_breaker(
    breaker: CircuitBreaker,
    retry: RetryWithBackoff | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: circuit breaker + retry."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not breaker.can_execute():
                raise CircuitOpenError(
                    f"Circuit '{breaker.name}' is open"
                )

            async def _call() -> Any:
                return await func(*args, **kwargs)

            try:
                if retry:
                    result = await retry.execute(_call)
                else:
                    result = await _call()
                breaker._on_success()
                return result
            except CircuitOpenError:
                raise
            except Exception as exc:
                breaker._on_failure()
                raise

        return wrapper

    return decorator
