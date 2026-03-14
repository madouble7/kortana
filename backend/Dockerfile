# ============================================
# Kor'tana Backend - Production Dockerfile
# ============================================
# Multi-stage build for optimized Python backend

# Stage 1: Builder
FROM python:3.11.7-slim AS builder

WORKDIR /build

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies to user site-packages with build cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.11.7-slim

# Set labels for metadata
LABEL maintainer="Kor'tana Team" \
      description="Kor'tana Backend API Service" \
      version="1.0.0"

# Create non-root user for security
RUN groupadd -r kortana && useradd -r -g kortana -u 1000 -m kortana

WORKDIR /app

# Install runtime dependencies only
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/kortana/.local

# Set environment variables
ENV PATH=/home/kortana/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Copy application code with proper ownership
COPY --chown=kortana:kortana . .

# Switch to non-root user
USER kortana

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "src.kortana.main:app", "--host", "0.0.0.0", "--port", "8000"]
