"""
Universal Enterprise Integration Framework for Cortex Core Enterprise.

This module provides a superior, universal integration layer that can connect
Cortex Core Enterprise to ANY enterprise monitoring platform in the world.
No longer limited to specific vendors - this system adapts to any infrastructure.
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import requests
import structlog
from prometheus_client import Gauge, Counter, Histogram, generate_latest, CollectorRegistry


class MetricFormat(Enum):
    """Supported metric export formats."""
    PROMETHEUS = "prometheus"
    STATSD = "statsd"
    DOGSTATSD = "dogstatsd"
    CLOUDWATCH = "cloudwatch"
    GRAPHITE = "graphite"
    JSON = "json"
    CUSTOM = "custom"


class AlertFormat(Enum):
    """Supported alert webhook formats."""
    PAGERDUTY = "pagerduty"
    SLACK = "slack"
    TEAMS = "teams"
    GENERIC = "generic"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"


class AlertSeverity(Enum):
    """Universal alert severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class UniversalMetric:
    """Universal metric data structure."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]
    metric_type: str = "gauge"  # gauge, counter, histogram


@dataclass
class UniversalAlert:
    """Universal alert data structure."""
    title: str
    description: str
    severity: AlertSeverity
    source: str
    timestamp: float
    tags: Dict[str, str]
    runbook_url: Optional[str] = None
    alert_id: Optional[str] = None


class MetricsExporter(ABC):
    """Abstract base class for metrics exporters."""

    @abstractmethod
    def export_metric(self, metric: UniversalMetric) -> bool:
        """Export a single metric."""
        pass

    @abstractmethod
    def export_batch(self, metrics: List[UniversalMetric]) -> bool:
        """Export a batch of metrics."""
        pass

    @abstractmethod
    def get_format(self) -> MetricFormat:
        """Return the supported metric format."""
        pass


class AlertDispatcher(ABC):
    """Abstract base class for alert dispatchers."""

    @abstractmethod
    def dispatch_alert(self, alert: UniversalAlert) -> bool:
        """Dispatch a single alert."""
        pass

    @abstractmethod
    def dispatch_batch(self, alerts: List[UniversalAlert]) -> bool:
        """Dispatch a batch of alerts."""
        pass

    @abstractmethod
    def get_format(self) -> AlertFormat:
        """Return the supported alert format."""
        pass


class PrometheusExporter(MetricsExporter):
    """Prometheus metrics exporter."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self.gauges: Dict[str, Gauge] = {}
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}

    def export_metric(self, metric: UniversalMetric) -> bool:
        try:
            if metric.metric_type == "gauge":
                if metric.name not in self.gauges:
                    self.gauges[metric.name] = Gauge(
                        metric.name,
                        f"Cortex Core {metric.name}",
                        labelnames=list(metric.tags.keys()),
                        registry=self.registry
                    )
                if metric.tags:
                    self.gauges[metric.name].labels(**metric.tags).set(metric.value)
                else:
                    self.gauges[metric.name].set(metric.value)
            elif metric.metric_type == "counter":
                if metric.name not in self.counters:
                    self.counters[metric.name] = Counter(
                        metric.name,
                        f"Cortex Core {metric.name}",
                        labelnames=list(metric.tags.keys()),
                        registry=self.registry
                    )
                if metric.tags:
                    self.counters[metric.name].labels(**metric.tags).inc(metric.value)
                else:
                    self.counters[metric.name].inc(metric.value)
            return True
        except Exception as e:
            logging.error(f"Failed to export metric to Prometheus: {e}")
            return False

    def export_batch(self, metrics: List[UniversalMetric]) -> bool:
        success = True
        for metric in metrics:
            if not self.export_metric(metric):
                success = False
        return success

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        return generate_latest(self.registry).decode('utf-8')

    def get_format(self) -> MetricFormat:
        return MetricFormat.PROMETHEUS


class StatsDExporter(MetricsExporter):
    """StatsD metrics exporter."""

    def __init__(self, host: str = "localhost", port: int = 8125):
        self.host = host
        self.port = port
        self.socket = None

    def _get_socket(self):
        if self.socket is None:
            import socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self.socket

    def export_metric(self, metric: UniversalMetric) -> bool:
        try:
            tags_str = ",".join(f"{k}={v}" for k, v in metric.tags.items())
            if tags_str:
                metric_line = f"{metric.name}:{metric.value}|g|#{tags_str}"
            else:
                metric_line = f"{metric.name}:{metric.value}|g"

            self._get_socket().sendto(
                metric_line.encode(),
                (self.host, self.port)
            )
            return True
        except Exception as e:
            logging.error(f"Failed to export metric to StatsD: {e}")
            return False

    def export_batch(self, metrics: List[UniversalMetric]) -> bool:
        success = True
        for metric in metrics:
            if not self.export_metric(metric):
                success = False
        return success

    def get_format(self) -> MetricFormat:
        return MetricFormat.STATSD


class DogStatsDExporter(StatsDExporter):
    """DataDog DogStatsD metrics exporter."""

    def export_metric(self, metric: UniversalMetric) -> bool:
        try:
            tags_str = "|".join(f"#{k}:{v}" for k, v in metric.tags.items())
            metric_line = f"{metric.name}:{metric.value}|g|{tags_str}"

            self._get_socket().sendto(
                metric_line.encode(),
                (self.host, self.port)
            )
            return True
        except Exception as e:
            logging.error(f"Failed to export metric to DogStatsD: {e}")
            return False

    def get_format(self) -> MetricFormat:
        return MetricFormat.DOGSTATSD


class PagerDutyDispatcher(AlertDispatcher):
    """PagerDuty alert dispatcher."""

    def __init__(self, routing_key: str, api_url: str = "https://events.pagerduty.com/v2/enqueue"):
        self.routing_key = routing_key
        self.api_url = api_url

    def dispatch_alert(self, alert: UniversalAlert) -> bool:
        try:
            severity_map = {
                AlertSeverity.CRITICAL: "critical",
                AlertSeverity.ERROR: "error",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.INFO: "info"
            }

            payload = {
                "routing_key": self.routing_key,
                "event_action": "trigger",
                "dedup_key": alert.alert_id or f"cortex-{alert.title}-{int(alert.timestamp)}",
                "payload": {
                    "summary": alert.title,
                    "source": alert.source,
                    "severity": severity_map.get(alert.severity, "info"),
                    "timestamp": alert.timestamp,
                    "component": "cortex-core",
                    "group": "ai-systems",
                    "class": "cortex-alert",
                    "custom_details": {
                        "description": alert.description,
                        "tags": alert.tags,
                        "runbook_url": alert.runbook_url
                    }
                }
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 202
        except Exception as e:
            logging.error(f"Failed to dispatch alert to PagerDuty: {e}")
            return False

    def dispatch_batch(self, alerts: List[UniversalAlert]) -> bool:
        success = True
        for alert in alerts:
            if not self.dispatch_alert(alert):
                success = False
        return success

    def get_format(self) -> AlertFormat:
        return AlertFormat.PAGERDUTY


class SlackDispatcher(AlertDispatcher):
    """Slack alert dispatcher."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def dispatch_alert(self, alert: UniversalAlert) -> bool:
        try:
            color_map = {
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.ERROR: "danger",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.INFO: "good"
            }

            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, "good"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Time", "value": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp)), "short": True}
                    ],
                    "footer": "Cortex Core Enterprise"
                }]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to dispatch alert to Slack: {e}")
            return False

    def dispatch_batch(self, alerts: List[UniversalAlert]) -> bool:
        success = True
        for alert in alerts:
            if not self.dispatch_alert(alert):
                success = False
        return success

    def get_format(self) -> AlertFormat:
        return AlertFormat.SLACK


class GenericWebhookDispatcher(AlertDispatcher):
    """Generic webhook alert dispatcher for any platform."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None,
                 template: Optional[Dict[str, Any]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.template = template or {}

    def dispatch_alert(self, alert: UniversalAlert) -> bool:
        try:
            payload = {
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "source": alert.source,
                "timestamp": alert.timestamp,
                "tags": alert.tags,
                "alert_id": alert.alert_id,
                "runbook_url": alert.runbook_url
            }

            # Merge with custom template
            payload.update(self.template)

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            return response.status_code < 300
        except Exception as e:
            logging.error(f"Failed to dispatch alert to webhook: {e}")
            return False

    def dispatch_batch(self, alerts: List[UniversalAlert]) -> bool:
        success = True
        for alert in alerts:
            if not self.dispatch_alert(alert):
                success = False
        return success

    def get_format(self) -> AlertFormat:
        return AlertFormat.GENERIC


class UniversalIntegrationManager:
    """
    Universal Integration Manager - The superior integration layer that
    connects Cortex Core Enterprise to ANY enterprise monitoring platform.
    """

    def __init__(self):
        self.metrics_exporters: Dict[str, MetricsExporter] = {}
        self.alert_dispatchers: Dict[str, AlertDispatcher] = {}
        self.metric_buffer: List[UniversalMetric] = []
        self.alert_buffer: List[UniversalAlert] = []
        self.buffer_lock = threading.Lock()
        self.export_thread: Optional[threading.Thread] = None
        self.running = False
        # Seconds to sleep between retries when the background export loop
        # encounters an error. Configurable so tests don't have to wait 5s.
        self.error_sleep: float = 5.0

        # Initialize default exporters
        self._setup_default_exporters()

    def _setup_default_exporters(self):
        """Setup default exporters for common platforms."""
        # Prometheus is always available
        self.register_metrics_exporter("prometheus", PrometheusExporter())

    def register_metrics_exporter(self, name: str, exporter: MetricsExporter):
        """Register a metrics exporter."""
        self.metrics_exporters[name] = exporter
        logging.info(f"Registered metrics exporter: {name} ({exporter.get_format().value})")

    def register_alert_dispatcher(self, name: str, dispatcher: AlertDispatcher):
        """Register an alert dispatcher."""
        self.alert_dispatchers[name] = dispatcher
        logging.info(f"Registered alert dispatcher: {name} ({dispatcher.get_format().value})")

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None,
                     metric_type: str = "gauge"):
        """Record a metric for export."""
        metric = UniversalMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metric_type=metric_type
        )

        with self.buffer_lock:
            self.metric_buffer.append(metric)

    def record_alert(self, title: str, description: str, severity: AlertSeverity,
                    source: str = "cortex-core", tags: Optional[Dict[str, str]] = None,
                    runbook_url: Optional[str] = None, alert_id: Optional[str] = None):
        """Record an alert for dispatch."""
        alert = UniversalAlert(
            title=title,
            description=description,
            severity=severity,
            source=source,
            timestamp=time.time(),
            tags=tags or {},
            runbook_url=runbook_url,
            alert_id=alert_id
        )

        with self.buffer_lock:
            self.alert_buffer.append(alert)

    def export_metrics(self, exporter_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Export metrics to specified exporters (or all if None)."""
        results = {}

        exporters = self.metrics_exporters
        if exporter_names:
            exporters = {name: self.metrics_exporters[name] for name in exporter_names
                        if name in self.metrics_exporters}

        with self.buffer_lock:
            metrics_to_export = self.metric_buffer.copy()
            self.metric_buffer.clear()

        for name, exporter in exporters.items():
            try:
                success = exporter.export_batch(metrics_to_export)
                results[name] = success
            except Exception as e:
                logging.error(f"Failed to export metrics to {name}: {e}")
                results[name] = False

        return results

    def dispatch_alerts(self, dispatcher_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Dispatch alerts to specified dispatchers (or all if None)."""
        results = {}

        dispatchers = self.alert_dispatchers
        if dispatcher_names:
            dispatchers = {name: self.alert_dispatchers[name] for name in dispatcher_names
                          if name in self.alert_dispatchers}

        with self.buffer_lock:
            alerts_to_dispatch = self.alert_buffer.copy()
            self.alert_buffer.clear()

        for name, dispatcher in dispatchers.items():
            try:
                success = dispatcher.dispatch_batch(alerts_to_dispatch)
                results[name] = success
            except Exception as e:
                logging.error(f"Failed to dispatch alerts to {name}: {e}")
                results[name] = False

        return results

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        prometheus = self.metrics_exporters.get("prometheus")
        if prometheus and isinstance(prometheus, PrometheusExporter):
            return prometheus.get_metrics_text()
        return ""

    def start_background_export(self, interval: int = 60):
        """Start background metric export and alert dispatch."""
        if self.running:
            return

        self.running = True
        self.export_thread = threading.Thread(
            target=self._background_export_loop,
            args=(interval,),
            daemon=True
        )
        self.export_thread.start()
        logging.info(f"Started background export with {interval}s interval")

    def stop_background_export(self):
        """Stop background export."""
        self.running = False
        if self.export_thread:
            self.export_thread.join(timeout=5)
        logging.info("Stopped background export")

    def _background_export_loop(self, interval: int):
        """Background export loop."""
        while self.running:
            try:
                self.export_metrics()
                self.dispatch_alerts()
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Error in background export loop: {e}")
                time.sleep(self.error_sleep)

    def configure_from_config(self, config: Dict[str, Any]):
        """Configure integrations from configuration."""
        # Configure metrics exporters
        if "metrics" in config:
            metrics_config = config["metrics"]
            for exporter_name, exporter_config in metrics_config.items():
                if exporter_config.get("enabled", False):
                    self._create_exporter_from_config(exporter_name, exporter_config)

        # Configure alert dispatchers
        if "alerts" in config:
            alerts_config = config["alerts"]
            for dispatcher_name, dispatcher_config in alerts_config.items():
                if dispatcher_config.get("enabled", False):
                    self._create_dispatcher_from_config(dispatcher_name, dispatcher_config)

    def _create_exporter_from_config(self, name: str, config: Dict[str, Any]):
        """Create exporter from configuration."""
        exporter_type = config.get("type", "").lower()

        if exporter_type == "prometheus":
            exporter = PrometheusExporter()
        elif exporter_type == "statsd":
            exporter = StatsDExporter(
                host=config.get("host", "localhost"),
                port=config.get("port", 8125)
            )
        elif exporter_type == "dogstatsd":
            exporter = DogStatsDExporter(
                host=config.get("host", "localhost"),
                port=config.get("port", 8125)
            )
        else:
            logging.warning(f"Unknown exporter type: {exporter_type}")
            return

        self.register_metrics_exporter(name, exporter)

    def _create_dispatcher_from_config(self, name: str, config: Dict[str, Any]):
        """Create dispatcher from configuration."""
        dispatcher_type = config.get("type", "").lower()

        if dispatcher_type == "pagerduty":
            dispatcher = PagerDutyDispatcher(
                routing_key=config["routing_key"],
                api_url=config.get("api_url", "https://events.pagerduty.com/v2/enqueue")
            )
        elif dispatcher_type == "slack":
            dispatcher = SlackDispatcher(webhook_url=config["webhook_url"])
        elif dispatcher_type == "generic":
            dispatcher = GenericWebhookDispatcher(
                webhook_url=config["webhook_url"],
                headers=config.get("headers"),
                template=config.get("template")
            )
        else:
            logging.warning(f"Unknown dispatcher type: {dispatcher_type}")
            return

        self.register_alert_dispatcher(name, dispatcher)


# Global integration manager instance
integration_manager = UniversalIntegrationManager()
