"""Circuit Breaker — prevents cascading failures for external services.

States:
  CLOSED    — normal operation, calls pass through
  OPEN      — service is failing, calls rejected immediately for 5 minutes
  HALF_OPEN — cooldown expired, one trial call allowed
"""

import asyncio
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

_FAILURE_THRESHOLD = 3
_RECOVERY_TIMEOUT = 300  # 5 minutes


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""

    def __init__(self, service: str) -> None:
        super().__init__(f"Circuit breaker OPEN for service '{service}'")
        self.service = service


class CircuitBreaker:
    """Circuit breaker for a named external service."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._opened_at and time.monotonic() - self._opened_at >= _RECOVERY_TIMEOUT:
                logger.info("circuit_breaker[%s]: transitioning OPEN → HALF_OPEN", self.service_name)
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def is_available(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def _record_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            logger.info("circuit_breaker[%s]: trial call succeeded → CLOSED", self.service_name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None

    def _record_failure(self) -> None:
        self._failure_count += 1
        logger.warning(
            "circuit_breaker[%s]: failure %d/%d",
            self.service_name,
            self._failure_count,
            _FAILURE_THRESHOLD,
        )
        if self._failure_count >= _FAILURE_THRESHOLD or self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()
            logger.error(
                "circuit_breaker[%s]: OPEN — will retry after %ds",
                self.service_name,
                _RECOVERY_TIMEOUT,
            )

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Wrap an async function call with circuit breaker logic."""
        if not self.is_available:
            raise CircuitOpenError(self.service_name)

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except CircuitOpenError:
            raise
        except Exception as exc:
            self._record_failure()
            raise exc


# Pre-built instances for known external services
meta_circuit = CircuitBreaker("meta")
claude_circuit = CircuitBreaker("claude")
