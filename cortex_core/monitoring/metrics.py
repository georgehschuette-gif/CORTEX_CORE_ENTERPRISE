"""
Metrics collection for Cortex Core.
"""

import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
except ImportError:
    # Fallback if prometheus_client not available
    class Counter:
        def __init__(self, name, description, labelnames=None, registry=None):
            self.name = name
            self._value = 0

        def inc(self, amount=1):
            self._value += amount

        def labels(self, **kwargs):
            return self

    class Gauge:
        def __init__(self, name, description, registry=None):
            self.name = name
            self._value = 0

        def set(self, value):
            self._value = value

    class Histogram:
        def __init__(self, name, description, buckets=None, registry=None):
            self.name = name
            self._observations = []

        def observe(self, value):
            self._observations.append(value)

    class CollectorRegistry:
        pass


class MetricsCollector:
    """
    Collects and exposes metrics for Cortex Core.
    """

    def __init__(self, retention_hours: int = 24):
        self.registry = CollectorRegistry()
        self.retention_hours = retention_hours

        # Prometheus metrics
        self.requests_total = Counter(
            "cortex_requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.requests_duration = Histogram(
            "cortex_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry,
        )

        self.active_connections = Gauge(
            "cortex_active_connections",
            "Number of active connections",
            registry=self.registry,
        )

        self.processing_time = Histogram(
            "cortex_processing_time_seconds",
            "Intelligence processing time",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "cortex_memory_usage_bytes", "Memory usage in bytes", registry=self.registry
        )

        # Internal metrics storage
        self._metrics_history = deque(maxlen=10000)
        self._lock = threading.Lock()

        # Start background cleanup
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def start(self):
        """Start metrics collection."""
        self._running = True
        self._cleanup_thread.start()

    def stop(self):
        """Stop metrics collection."""
        self._running = False

    def record_request(
        self, endpoint: str, method: str, status_code: int, processing_time: float = 0
    ):
        """
        Record an API request.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            processing_time: Request processing time
        """
        # Prometheus metrics
        self.requests_total.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()

        self.requests_duration.labels(method=method, endpoint=endpoint).observe(
            processing_time
        )

        # Internal storage
        with self._lock:
            self._metrics_history.append(
                {
                    "timestamp": datetime.utcnow(),
                    "type": "request",
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "processing_time": processing_time,
                }
            )

    def record_processing(self, component: str, duration: float, success: bool):
        """
        Record processing metrics.

        Args:
            component: Processing component
            duration: Processing duration
            success: Whether processing was successful
        """
        self.processing_time.observe(duration)

        with self._lock:
            self._metrics_history.append(
                {
                    "timestamp": datetime.utcnow(),
                    "type": "processing",
                    "component": component,
                    "duration": duration,
                    "success": success,
                }
            )

    def update_memory_usage(self, usage_bytes: int):
        """
        Update memory usage metric.

        Args:
            usage_bytes: Current memory usage in bytes
        """
        self.memory_usage.set(usage_bytes)

    def update_active_connections(self, count: int):
        """
        Update active connections count.

        Args:
            count: Number of active connections
        """
        self.active_connections.set(count)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.

        Returns:
            Summary statistics
        """
        with self._lock:
            if not self._metrics_history:
                return {
                    "total_requests": 0,
                    "avg_processing_time": 0,
                    "success_rate": 0,
                    "requests_per_minute": 0,
                }

            # Calculate statistics
            requests = [m for m in self._metrics_history if m["type"] == "request"]
            processing = [m for m in self._metrics_history if m["type"] == "processing"]

            total_requests = len(requests)
            successful_requests = len(
                [r for r in requests if 200 <= r["status_code"] < 400]
            )

            if requests:
                total_processing_time = sum(
                    r.get("processing_time", 0) for r in requests
                )
                avg_processing_time = total_processing_time / len(requests)
                success_rate = successful_requests / len(requests)
            else:
                avg_processing_time = 0
                success_rate = 0

            # Calculate requests per minute (last hour)
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            recent_requests = [r for r in requests if r["timestamp"] > last_hour]
            requests_per_minute = len(recent_requests) / 60

            return {
                "total_requests": total_requests,
                "avg_processing_time": avg_processing_time,
                "success_rate": success_rate,
                "requests_per_minute": requests_per_minute,
                "total_processing_events": len(processing),
            }

    def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        # This is a simplified implementation
        # In a real system, you'd use the prometheus_client library
        summary = self.get_summary()

        metrics = f"""# HELP cortex_requests_total Total number of requests
# TYPE cortex_requests_total counter
cortex_requests_total {summary['total_requests']}

# HELP cortex_avg_processing_time_seconds Average processing time
# TYPE cortex_avg_processing_time_seconds gauge
cortex_avg_processing_time_seconds {summary['avg_processing_time']}

# HELP cortex_success_rate Request success rate
# TYPE cortex_success_rate gauge
cortex_success_rate {summary['success_rate']}

# HELP cortex_requests_per_minute Requests per minute
# TYPE cortex_requests_per_minute gauge
cortex_requests_per_minute {summary['requests_per_minute']}
"""

        return metrics

    def _cleanup_loop(self):
        """Background cleanup loop."""
        while getattr(self, "_running", True):
            try:
                self._cleanup_old_metrics()
                time.sleep(300)  # Clean up every 5 minutes
            except Exception as e:
                print(f"Metrics cleanup error: {e}")
                time.sleep(60)

    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)

        with self._lock:
            # Remove old entries
            while (
                self._metrics_history and self._metrics_history[0]["timestamp"] < cutoff
            ):
                self._metrics_history.popleft()
