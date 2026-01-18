# ============================================
# Kor'tana Backend - Production Dockerfile
# ============================================
# Multi-stage build for optimized Python backend

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies to user site-packages
RUN pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set labels for metadata
LABEL maintainer="Kor'tana Team"
LABEL description="Kor'tana Backend API Service"
LABEL version="1.0.0"

# Create non-root user for security
RUN groupadd -r kortana && useradd -r -g kortana -u 1000 kortana

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/kortana/.local

# Set PATH for user-installed packages
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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
