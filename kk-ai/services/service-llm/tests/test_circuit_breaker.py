"""Tests for circuit breaker and retry mechanism."""

import asyncio

import pytest

from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    RetryWithBackoff,
)


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_success() -> None:
    """Test circuit breaker stays closed after successful calls."""
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=1.0)

    async def success_func():
        return "ok"

    for _ in range(5):
        result = await cb.call(success_func)
        assert result == "ok"

    assert cb.state.value == "closed"
    assert cb.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    """Test circuit breaker opens after threshold failures."""
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=30.0)

    async def fail_func():
        raise ValueError("boom")

    # First 2 failures should not open
    for _ in range(2):
        with pytest.raises(ValueError):
            await cb.call(fail_func)
    assert cb.state.value == "closed"

    # 3rd failure opens the circuit
    with pytest.raises(ValueError):
        await cb.call(fail_func)
    assert cb.state.value == "open"

    # Next call should raise CircuitOpenError
    with pytest.raises(CircuitOpenError):
        await cb.call(fail_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery() -> None:
    """Test circuit breaker transitions to half-open then closed."""
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1)

    async def fail_func():
        raise ValueError("boom")

    # Open the circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            await cb.call(fail_func)
    assert cb.state.value == "open"

    # Wait for recovery timeout
    await asyncio.sleep(0.2)

    # Circuit should be half-open, success closes it
    async def success_func():
        return "ok"

    result = await cb.call(success_func)
    assert result == "ok"
    assert cb.state.value == "closed"


@pytest.mark.asyncio
async def test_retry_with_backoff_success() -> None:
    """Test retry succeeds on second attempt."""
    retry = RetryWithBackoff(max_attempts=3, base_delay=0.1)

    call_count = 0

    async def sometimes_fails():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("temp error")
        return "ok"

    result = await retry.execute(sometimes_fails)
    assert result == "ok"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_with_backoff_exhausted() -> None:
    """Test retry fails after all attempts exhausted."""
    retry = RetryWithBackoff(max_attempts=2, base_delay=0.1)

    async def always_fails():
        raise ValueError("persistent error")

    with pytest.raises(ValueError, match="persistent error"):
        await retry.execute(always_fails)


@pytest.mark.asyncio
async def test_circuit_breaker_status() -> None:
    """Test circuit breaker status report."""
    cb = CircuitBreaker(name="status-test", failure_threshold=5, recovery_timeout=30.0)
    status = cb.get_status()

    assert status["name"] == "status-test"
    assert status["state"] == "closed"
    assert status["failure_threshold"] == 5
    assert status["failure_count"] == 0
