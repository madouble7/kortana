# ============================================
# Kor'tana Backend - Production Dockerfile
# ============================================
# Multi-stage build for optimized Python backend

# Stage 1: Builder
FROM python:3.11.7-slim AS builder

WORKDIR /build

# Install build dependencies with cache mounts
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with aggressive caching and optimization
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install --user \
    --no-warn-script-location \
    --no-cache-dir \
    --compile \
    -r requirements.txt && \
    find /root/.local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type f -name "*.pyc" -delete && \
    find /root/.local -type f -name "*.pyo" -delete

# Stage 2: Runtime
FROM python:3.11.7-slim

# Set labels for metadata
LABEL maintainer="Kor'tana Team" \
    description="Kor'tana Backend API Service" \
    version="1.0.0"

# Create non-root user for security with minimal capabilities
RUN groupadd -r kortana && useradd -r -g kortana -u 1000 -m kortana

WORKDIR /app

# Install runtime dependencies with cache mounts and cleanup
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libpq5 \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python dependencies from builder with verification
COPY --from=builder --chown=kortana:kortana /root/.local /home/kortana/.local

# Set environment variables
ENV PATH=/home/kortana/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_INPUT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy application code with proper ownership and minimal layers
COPY --chown=kortana:kortana . .

# Set read-only root filesystem compatibility
RUN mkdir -p /app/tmp /app/logs && \
    chown -R kortana:kortana /app/tmp /app/logs && \
    chmod 755 /app/tmp /app/logs

# Switch to non-root user
USER kortana

# Expose port
EXPOSE 8000

# Health check with stricter parameters
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application with optimized settings
CMD ["uvicorn", \
    "src.kortana.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--log-level", "info", \
    "--access-log"]
