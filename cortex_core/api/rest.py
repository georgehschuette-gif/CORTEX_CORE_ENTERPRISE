"""
REST API for Cortex Core.
"""

import logging
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from cortex_core.core.factory import create_cortex
from cortex_core.exceptions import CortexError, SecurityError, ValidationError
from cortex_core.monitoring.metrics import MetricsCollector
from cortex_core.security.auth.jwt_manager import JWTManager

logger = logging.getLogger(__name__)

# Pydantic models


class ProcessRequest(BaseModel):
    """Request model for intelligence processing."""

    data: Dict[str, Any] = Field(..., description="Intelligence data to process")
    validate: bool = Field(True, description="Whether to validate input")
    priority: str = Field("normal", description="Processing priority")


class ProcessResponse(BaseModel):
    """Response model for processing results."""

    success: bool
    decision: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    memory_id: Optional[str] = None
    processing_time: Optional[float] = None
    component_times: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str


# FastAPI app
app = FastAPI(
    title="Cortex Core Enterprise API",
    description="Advanced Neural-Symbolic AI System with Security & Autonomy",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
security = HTTPBearer(auto_error=False)
jwt_manager = JWTManager()
metrics = MetricsCollector()

# Global Cortex Core instance
cortex_core = None


def get_cortex_core():
    """Get or create Cortex Core instance."""
    global cortex_core
    if cortex_core is None:
        cortex_core = create_cortex()
    return cortex_core


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user."""
    if not credentials:
        return None

    try:
        payload = jwt_manager.decode_token(credentials.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


# Routes


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        core = get_cortex_core()
        status = core.get_status()

        return HealthResponse(
            status="healthy" if status["status"] == "operational" else "unhealthy",
            version=status["version"],
            timestamp="2024-01-15T10:30:00Z",  # Would be dynamic in real implementation
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/process", response_model=ProcessResponse)
async def process_intelligence(
    request: ProcessRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Process intelligence data.

    Requires authentication for production use.
    """
    try:
        # Get Cortex Core instance
        core = get_cortex_core()

        # Process the data
        result = core.process(data=request.data, validate=request.validate)

        # Record metrics
        metrics.record_request(
            endpoint="/process",
            method="POST",
            status_code=200 if result["success"] else 500,
            processing_time=result.get("processing_time", 0),
        )

        if result["success"]:
            return ProcessResponse(**result)
        else:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Processing failed")
            )

    except SecurityError as e:
        logger.warning(f"Security error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except CortexError as e:
        logger.error(f"Cortex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/status")
async def get_system_status(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Get system status."""
    try:
        core = get_cortex_core()
        status = core.get_status()

        return {
            "status": status,
            "metrics": metrics.get_summary(),
            "timestamp": "2024-01-15T10:30:00Z",
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@app.get("/metrics")
async def get_metrics():
    """Get system metrics (Prometheus format)."""
    return metrics.get_prometheus_metrics()


# Startup and shutdown events


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    global cortex_core
    logger.info("Cortex Core API starting up...")

    # Initialize global Cortex Core instance
    cortex_core = create_cortex()

    # Start metrics collection
    metrics.start()

    logger.info("Cortex Core API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("Cortex Core API shutting down...")

    # Shutdown Cortex Core
    if cortex_core:
        cortex_core.shutdown()

    # Stop metrics collection
    metrics.stop()

    logger.info("Cortex Core API shutdown complete")


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "cortex_core.api.rest:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
