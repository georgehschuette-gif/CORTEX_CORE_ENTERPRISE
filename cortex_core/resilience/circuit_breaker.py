"""
Circuit Breaker pattern implementation.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.

    Prevents cascading failures by stopping requests
    when failure rate exceeds threshold.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_attempts: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_attempts = 0

        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}")

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        self.total_requests += 1

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (
                    datetime.utcnow() - self.last_failure_time
                ).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self._transition_to_half_open()
                    return True
            return False

        return True

    def record_success(self):
        """Record successful request."""
        self.successful_requests += 1

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_attempts += 1

            if self.half_open_attempts >= self.half_open_max_attempts:
                self._transition_to_closed()

        # Reset failure count on success streak
        if self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        """Record failed request."""
        self.failed_requests += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.half_open_attempts = 0

        logger.warning(f"Circuit breaker transitioned from {old_state} to OPEN")

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.half_open_attempts = 0

        logger.info(f"Circuit breaker transitioned from {old_state} to HALF_OPEN")

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0

        logger.info(f"Circuit breaker transitioned from {old_state} to CLOSED")

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics."""
        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0
            else 0
        )

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "half_open_attempts": self.half_open_attempts,
        }

    async def execute(
        self, func: Callable, fallback: Optional[Callable] = None, *args, **kwargs
    ):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            fallback: Fallback function if circuit is open
            *args, **kwargs: Function arguments

        Returns:
            Function result or fallback result

        Raises:
            Exception: If execution fails and no fallback
        """
        import asyncio

        if not self.allow_request():
            if fallback:
                logger.warning("Circuit open, using fallback")
                return (
                    fallback(*args, **kwargs)
                    if not asyncio.iscoroutinefunction(fallback)
                    else await fallback(*args, **kwargs)
                )
            raise Exception("Circuit breaker is open")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self.record_success()
            return result

        except Exception as e:
            self.record_failure()
            logger.error(f"Circuit breaker caught error: {e}")

            if fallback:
                return (
                    fallback(*args, **kwargs)
                    if not asyncio.iscoroutinefunction(fallback)
                    else await fallback(*args, **kwargs)
                )
            raise
