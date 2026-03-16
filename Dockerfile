## syntax=docker/dockerfile:1.7
# Multi-stage build for Kor'tana Unified Platform

# --- Stage 1: Frontend Build ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Backend Builder ---
FROM python:3.11-slim AS backend-builder
WORKDIR /build
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir --compile -r requirements.txt

# --- Stage 3: Final Production Image ---
FROM python:3.11-slim AS runtime
WORKDIR /app

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r kortana && useradd -r -g kortana -u 1000 -m kortana

# Copy Python dependencies from builder
COPY --from=backend-builder /root/.local /home/kortana/.local
ENV PATH=/home/kortana/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Copy backend application code
COPY --chown=kortana:kortana backend/ ./

# Copy built frontend assets to backend static directory
COPY --from=frontend-builder --chown=kortana:kortana /app/frontend/dist ./static

# Environment variables
ENV PORT=8000
ENV ENVIRONMENT=production

# Run as non-root
USER kortana

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "src.kortana.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
