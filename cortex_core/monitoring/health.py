"""
Health Monitor for Cortex Core.
"""

import logging
import threading
import time
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Health monitoring system for Cortex Core components.
    """

    def __init__(self, check_interval: int = 30, error_pause: float = 5):
        self.check_interval = check_interval
        self.error_pause = error_pause
        self.is_running = False
        self.thread = None
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.health_status: Dict[str, Any] = {}

        logger.info(f"Health Monitor initialized with {check_interval}s interval")

    def register_check(self, name: str, check_func: Callable[[], bool]):
        """
        Register a health check function.

        Args:
            name: Check name
            check_func: Function that returns True if healthy
        """
        self.health_checks[name] = check_func
        logger.debug(f"Registered health check: {name}")

    def start(self):
        """Start health monitoring."""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        logger.info("Health monitoring started")

    def stop(self):
        """Stop health monitoring."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)

        logger.info("Health monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self._perform_checks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.error_pause)  # Brief pause on error

    def _perform_checks(self):
        """Perform all registered health checks."""
        status = {}

        for name, check_func in self.health_checks.items():
            try:
                is_healthy = check_func()
                status[name] = {
                    "healthy": is_healthy,
                    "timestamp": time.time(),
                    "error": None,
                }
            except Exception as e:
                status[name] = {
                    "healthy": False,
                    "timestamp": time.time(),
                    "error": str(e),
                }

        self.health_status = status
        logger.debug(f"Health check completed: {len(status)} checks")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current health status.

        Returns:
            Health status dictionary
        """
        overall_healthy = all(
            check.get("healthy", False) for check in self.health_status.values()
        )

        return {
            "overall_healthy": overall_healthy,
            "checks": self.health_status,
            "timestamp": time.time(),
            "total_checks": len(self.health_checks),
        }

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.get_status()["overall_healthy"]
