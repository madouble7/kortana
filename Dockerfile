## syntax=docker/dockerfile:1.7
# Multi-stage build for Kor'tana Unified Platform - Development
# Optimized with BuildKit cache mounts and best practices

# --- Stage 1: Frontend Build ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit --no-fund

COPY frontend/ ./

RUN npm run build


# --- Stage 2: Backend Dependencies ---
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


# --- Stage 3: Runtime Base ---
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies only
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libpq5 \
    ca-certificates \
    postgresql-client \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r kortana && useradd -r -g kortana -u 1000 -m kortana

# Copy Python dependencies from builder stage
COPY --from=backend-builder --chown=kortana:kortana /root/.local /home/kortana/.local

# Copy backend application code
COPY --chown=kortana:kortana backend/ ./

# Copy built frontend assets
COPY --from=frontend-builder --chown=kortana:kortana /app/frontend/dist ./static

# Set environment variables
ENV PATH=/home/kortana/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Run as non-root user
USER kortana

# Configure git identity for autonomous commits
RUN git config --global user.email "kortana@kor-tana.ai" && \
    git config --global user.name "Kor'tana" && \
    git config --global init.defaultBranch main && \
    git config --global --add safe.directory '*'

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

# Start the application
CMD ["uvicorn", "src.kortana.main:app", "--host", "0.0.0.0", "--port", "8000"]
