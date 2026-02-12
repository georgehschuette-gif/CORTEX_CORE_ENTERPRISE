# Cortex Core Enterprise Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cortex && useradd -r -g cortex cortex

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-enterprise.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-enterprise.txt

# Copy source code
COPY cortex_core/ ./cortex_core/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p data logs && \
    chown -R cortex:cortex /app

# Switch to non-root user
USER cortex

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 8081

# Set default command
CMD ["python", "-m", "uvicorn", "cortex_core.api.rest:app", "--host", "0.0.0.0", "--port", "8080"]
