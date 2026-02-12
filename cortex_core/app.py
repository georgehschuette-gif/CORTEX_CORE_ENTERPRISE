"""
Cortex Core Enterprise - Universal AI Platform for Global Infrastructure

The superior, universal integration layer that connects advanced AI capabilities
to ANY enterprise monitoring platform in the world. No longer limited to specific
vendors - this system adapts to any infrastructure.
"""

import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cortex_core.core.factory import create_cortex
from cortex_core.config import load_config
from cortex_core.integration.api import EnterpriseAPI
from cortex_core.integration.logging import enterprise_logger

# Initialize enterprise logging
logger = enterprise_logger.get_logger("cortex_app")

# Create FastAPI application
app = FastAPI(
    title="Cortex Core Enterprise",
    description="Universal AI Platform for Global Enterprise Infrastructure",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Cortex Core instance
cortex_core = None

@app.on_event("startup")
async def startup_event():
    """Initialize Cortex Core on startup."""
    global cortex_core

    try:
        logger.info("Initializing Cortex Core Enterprise...")

        # Load configuration
        config = load_config()

        # Create Cortex Core instance
        cortex_core = create_cortex(config)

        # Initialize enterprise API
        enterprise_api = EnterpriseAPI(cortex_core, cortex_core.health_monitor)
        app.include_router(enterprise_api.router)

        logger.info("Cortex Core Enterprise initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Cortex Core: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown Cortex Core on shutdown."""
    global cortex_core

    if cortex_core:
        logger.info("Shutting down Cortex Core Enterprise...")
        cortex_core.shutdown()
        logger.info("Cortex Core Enterprise shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Cortex Core Enterprise",
        "description": "Universal AI Platform for Global Enterprise Infrastructure",
        "version": "1.0.0",
        "status": "operational",
        "supported_platforms": [
            "Prometheus", "DataDog", "PagerDuty", "Slack", "Microsoft Teams",
            "ELK Stack", "Splunk", "CloudWatch", "Graphite", "New Relic"
        ],
        "api_endpoints": {
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics",
            "alerts": "/api/v1/alerts/trigger",
            "integration": "/api/v1/integration/status",
            "docs": "/api/v1/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    if cortex_core:
        health_status = cortex_core.health_monitor.is_healthy()
        return {
            "status": "healthy" if health_status else "unhealthy",
            "service": "cortex-core-enterprise",
            "version": "1.0.0"
        }
    return {"status": "initializing"}

@app.post("/process")
async def process_intelligence(request: Request):
    """Process intelligence data."""
    if not cortex_core:
        return JSONResponse(
            status_code=503,
            content={"error": "Cortex Core not initialized"}
        )

    try:
        data = await request.json()
        result = cortex_core.process(data)
        return result
    except Exception as e:
        enterprise_logger.log_error(e, component="api")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__}
        )

@app.get("/platforms")
async def supported_platforms():
    """List all supported enterprise platforms."""
    return {
        "monitoring_platforms": [
            {
                "name": "Prometheus",
                "description": "Metrics collection and alerting",
                "endpoint": "/api/v1/metrics?format=prometheus",
                "documentation": "https://prometheus.io/docs/"
            },
            {
                "name": "DataDog",
                "description": "Cloud monitoring and analytics",
                "configuration": "integration.metrics.datadog.*",
                "documentation": "https://docs.datadoghq.com/"
            },
            {
                "name": "CloudWatch",
                "description": "AWS monitoring service",
                "configuration": "integration.metrics.cloudwatch.*",
                "documentation": "https://docs.aws.amazon.com/cloudwatch/"
            },
            {
                "name": "Graphite",
                "description": "Time-series data storage",
                "configuration": "integration.metrics.graphite.*",
                "documentation": "https://graphite.readthedocs.io/"
            }
        ],
        "alerting_platforms": [
            {
                "name": "PagerDuty",
                "description": "Incident response platform",
                "endpoint": "/api/v1/alerts/trigger",
                "configuration": "integration.alerts.pagerduty.*",
                "documentation": "https://developer.pagerduty.com/"
            },
            {
                "name": "Slack",
                "description": "Team communication platform",
                "endpoint": "/api/v1/alerts/trigger",
                "configuration": "integration.alerts.slack.*",
                "documentation": "https://api.slack.com/"
            },
            {
                "name": "Microsoft Teams",
                "description": "Microsoft collaboration platform",
                "endpoint": "/api/v1/alerts/trigger",
                "configuration": "integration.alerts.teams.*",
                "documentation": "https://docs.microsoft.com/en-us/microsoftteams/"
            }
        ],
        "logging_platforms": [
            {
                "name": "ELK Stack",
                "description": "Elasticsearch, Logstash, Kibana",
                "configuration": "integration.logging.destinations.*",
                "documentation": "https://www.elastic.co/elastic-stack"
            },
            {
                "name": "Splunk",
                "description": "Enterprise logging and analytics",
                "configuration": "integration.logging.destinations.*",
                "documentation": "https://docs.splunk.com/"
            },
            {
                "name": "Fluentd",
                "description": "Log collector and aggregator",
                "configuration": "integration.logging.destinations.*",
                "documentation": "https://docs.fluentd.org/"
            }
        ],
        "universal_integration": {
            "description": "Cortex Core Enterprise can integrate with ANY platform using our universal webhook and API system",
            "custom_webhook": "integration.alerts.generic_webhook.*",
            "custom_metrics": "integration.metrics.*",
            "custom_logging": "integration.logging.destinations.*"
        }
    }

def main():
    """Main entry point for Cortex Core Enterprise."""
    import argparse

    parser = argparse.ArgumentParser(description="Cortex Core Enterprise")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Cortex Core Enterprise on {args.host}:{args.port}")

    uvicorn.run(
        "cortex_core.app:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
