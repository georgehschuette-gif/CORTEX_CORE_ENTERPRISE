"""
Enterprise API Endpoints for Cortex Core Enterprise.

Provides RESTful APIs that ANY monitoring platform can integrate with,
making Cortex Core Enterprise universally compatible with global infrastructure.
"""

import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from cortex_core.monitoring.health import HealthMonitor
from cortex_core.core.cortex_core import CortexCore
from cortex_core.integration.universal import integration_manager, AlertSeverity


# Pydantic models for API responses
class HealthStatus(BaseModel):
    overall_healthy: bool
    checks: Dict[str, Any]
    timestamp: float
    total_checks: int


class MetricsResponse(BaseModel):
    metrics: Dict[str, Any]
    timestamp: float
    format: str = "json"


class AlertTrigger(BaseModel):
    title: str
    description: str
    severity: str
    source: str = "external-api"
    tags: Optional[Dict[str, str]] = None
    runbook_url: Optional[str] = None


class IntegrationStatus(BaseModel):
    metrics_exporters: Dict[str, bool]
    alert_dispatchers: Dict[str, bool]
    buffer_sizes: Dict[str, int]
    last_export: Optional[float] = None


class EnterpriseAPI:
    """
    Enterprise API Layer - Universal integration endpoints for any monitoring platform.
    """

    def __init__(self, cortex_core: CortexCore, health_monitor: HealthMonitor):
        self.cortex_core = cortex_core
        self.health_monitor = health_monitor
        self.router = APIRouter(prefix="/api/v1", tags=["enterprise"])
        self._setup_routes()
        self.last_export = None

    def _setup_routes(self):
        """Setup all API routes."""

        @self.router.get("/health", response_model=HealthStatus)
        async def get_health():
            """Universal health check endpoint for any monitoring system."""
            try:
                status = self.health_monitor.get_status()
                return HealthStatus(**status)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

        @self.router.get("/health/simple")
        async def get_simple_health():
            """Simple health check for load balancers and basic monitoring."""
            try:
                status = self.health_monitor.is_healthy()
                return {"status": "healthy" if status else "unhealthy", "timestamp": time.time()}
            except Exception:
                return {"status": "error", "timestamp": time.time()}

        @self.router.get("/metrics", response_model=MetricsResponse)
        async def get_metrics(format: str = Query("json", description="Metrics format")):
            """Universal metrics endpoint supporting multiple formats."""
            try:
                if format.lower() == "prometheus":
                    prometheus_metrics = integration_manager.get_prometheus_metrics()
                    return MetricsResponse(
                        metrics={"prometheus": prometheus_metrics},
                        timestamp=time.time(),
                        format="prometheus"
                    )
                elif format.lower() == "json":
                    # Get core metrics
                    core_metrics = {
                        "processing_count": len(self.cortex_core.metrics),
                        "total_duration": sum(m.get('duration', 0) for m in self.cortex_core.metrics[-100:]),
                        "success_rate": sum(1 for m in self.cortex_core.metrics[-100:] if m.get('success', False)) / max(len(self.cortex_core.metrics[-100:]), 1),
                        "memory_usage": len(self.cortex_core.metrics),  # Simplified
                        "uptime": time.time() - getattr(self.cortex_core, 'start_time', time.time())
                    }

                    # Add integration metrics
                    integration_metrics = {
                        "metrics_buffer_size": len(integration_manager.metric_buffer),
                        "alerts_buffer_size": len(integration_manager.alert_buffer),
                        "active_exporters": len(integration_manager.metrics_exporters),
                        "active_dispatchers": len(integration_manager.alert_dispatchers)
                    }

                    return MetricsResponse(
                        metrics={"core": core_metrics, "integration": integration_metrics},
                        timestamp=time.time(),
                        format="json"
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

        @self.router.post("/alerts/trigger")
        async def trigger_alert(alert: AlertTrigger):
            """Trigger an alert through the universal alerting system."""
            try:
                severity_map = {
                    "critical": AlertSeverity.CRITICAL,
                    "error": AlertSeverity.ERROR,
                    "warning": AlertSeverity.WARNING,
                    "info": AlertSeverity.INFO,
                    "debug": AlertSeverity.DEBUG
                }

                severity = severity_map.get(alert.severity.lower(), AlertSeverity.INFO)

                integration_manager.record_alert(
                    title=alert.title,
                    description=alert.description,
                    severity=severity,
                    source=alert.source,
                    tags=alert.tags,
                    runbook_url=alert.runbook_url
                )

                # Immediately dispatch alerts
                results = integration_manager.dispatch_alerts()
                success = any(results.values()) if results else False

                return {
                    "status": "alert_triggered" if success else "alert_queued",
                    "dispatch_results": results,
                    "timestamp": time.time()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Alert trigger failed: {str(e)}")

        @self.router.get("/integration/status", response_model=IntegrationStatus)
        async def get_integration_status():
            """Get status of all integration components."""
            try:
                # Check exporter health (simplified - in real implementation would test connections)
                exporter_status = {name: True for name in integration_manager.metrics_exporters.keys()}

                # Check dispatcher health
                dispatcher_status = {name: True for name in integration_manager.alert_dispatchers.keys()}

                return IntegrationStatus(
                    metrics_exporters=exporter_status,
                    alert_dispatchers=dispatcher_status,
                    buffer_sizes={
                        "metrics": len(integration_manager.metric_buffer),
                        "alerts": len(integration_manager.alert_buffer)
                    },
                    last_export=integration_manager.last_export if hasattr(integration_manager, 'last_export') else None
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Integration status check failed: {str(e)}")

        @self.router.post("/integration/export")
        async def trigger_export():
            """Manually trigger metrics export and alert dispatch."""
            try:
                metrics_results = integration_manager.export_metrics()
                alerts_results = integration_manager.dispatch_alerts()

                integration_manager.last_export = time.time()

                return {
                    "metrics_exported": len(integration_manager.metric_buffer) if hasattr(integration_manager, 'metric_buffer') else 0,
                    "alerts_dispatched": len(integration_manager.alert_buffer) if hasattr(integration_manager, 'alert_buffer') else 0,
                    "metrics_results": metrics_results,
                    "alerts_results": alerts_results,
                    "timestamp": time.time()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Export trigger failed: {str(e)}")

        @self.router.get("/info")
        async def get_system_info():
            """Get comprehensive system information for enterprise monitoring."""
            try:
                info = {
                    "system": "Cortex Core Enterprise",
                    "version": getattr(self.cortex_core, 'version', '1.0.0'),
                    "status": "operational",
                    "capabilities": [
                        "universal_metrics_export",
                        "universal_alert_dispatch",
                        "cognitive_processing",
                        "distributed_computing",
                        "enterprise_integration"
                    ],
                    "supported_platforms": [
                        "prometheus", "grafana", "datadog", "pagerduty",
                        "slack", "teams", "cloudwatch", "graphite",
                        "elasticsearch", "splunk", "new_relic", "app_dynamics"
                    ],
                    "api_endpoints": [
                        "/api/v1/health",
                        "/api/v1/health/simple",
                        "/api/v1/metrics",
                        "/api/v1/alerts/trigger",
                        "/api/v1/integration/status",
                        "/api/v1/integration/export",
                        "/api/v1/info"
                    ],
                    "timestamp": time.time(),
                    "uptime": time.time() - getattr(self.cortex_core, 'start_time', time.time())
                }
                return info
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"System info retrieval failed: {str(e)}")

        @self.router.get("/platforms")
        async def get_supported_platforms():
            """List all supported enterprise platforms and integration methods."""
            platforms = {
                "monitoring": [
                    {"name": "Prometheus", "format": "prometheus", "endpoint": "/metrics"},
                    {"name": "DataDog", "format": "dogstatsd", "port": 8125},
                    {"name": "StatsD", "format": "statsd", "port": 8125},
                    {"name": "CloudWatch", "format": "cloudwatch", "via": "boto3"},
                    {"name": "Graphite", "format": "graphite", "port": 2003}
                ],
                "alerting": [
                    {"name": "PagerDuty", "format": "pagerduty", "method": "webhook"},
                    {"name": "Slack", "format": "slack", "method": "webhook"},
                    {"name": "Microsoft Teams", "format": "teams", "method": "webhook"},
                    {"name": "Generic Webhook", "format": "generic", "method": "configurable"}
                ],
                "logging": [
                    {"name": "ELK Stack", "format": "json", "method": "structured"},
                    {"name": "Splunk", "format": "json", "method": "http_event_collector"},
                    {"name": "Graylog", "format": "gelf", "method": "udp/tcp"},
                    {"name": "Fluentd", "format": "json", "method": "forward"}
                ],
                "api_compatibility": [
                    {"name": "RESTful APIs", "version": "v1", "authentication": "configurable"},
                    {"name": "GraphQL", "status": "planned", "version": "future"},
                    {"name": "gRPC", "status": "planned", "version": "future"}
                ]
            }
            return platforms
