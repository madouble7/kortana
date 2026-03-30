# ============================================
# Hub Dispatcher - Dockerfile (Optimized)
# ============================================
# Multi-stage build for central message routing

FROM python:3.11-slim AS builder

WORKDIR /build

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir -r requirements.txt && \
    find /root/.local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type f -name "*.pyc" -delete

# Runtime
FROM python:3.11-slim

LABEL maintainer="Kor'tana Team" \
      description="Hub Dispatcher Service" \
      version="1.0.0"

RUN groupadd -r dispatcher && useradd -r -g dispatcher -u 1003 dispatcher && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder --chown=dispatcher:dispatcher /root/.local /home/dispatcher/.local

ENV PATH=/home/dispatcher/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

COPY --chown=dispatcher:dispatcher . .

USER dispatcher

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
