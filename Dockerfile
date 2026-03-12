# =============================================================================
# AION OS - Adversarial Intelligence Operating System
# Multi-stage Docker build for production deployment
# =============================================================================

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install cryptography PyJWT

# Stage 2: Production runtime
FROM python:3.12-slim AS runtime

LABEL maintainer="CodeTyphoons" \
      description="AION OS - Insider threat detection for law firms" \
      version="0.1.0"

# Security: run as non-root
RUN groupadd -r aion && useradd -r -g aion -m aion

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY aionos/ ./aionos/
COPY config/ ./config/
COPY requirements.txt .

# Create runtime directories
RUN mkdir -p aion_data/events aion_data/reports aion_data/documents \
             aion_data/policies aion_data/feedback logs \
    && chown -R aion:aion /app

# Environment defaults (override at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AION_LOG_LEVEL=INFO \
    AION_DATA_DIR=/app/aion_data \
    AION_HOST=0.0.0.0 \
    AION_PORT=8000

# Expose API port + metrics
EXPOSE 8000

# Health check: hit /health every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER aion

# Run the API server
CMD ["python", "-m", "uvicorn", "aionos.api.rest_api:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
