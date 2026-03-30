# ============================================
# Heartbeat Service - Dockerfile (Optimized)
# ============================================
# Multi-stage build for minimal footprint

FROM python:3.11-alpine AS builder

WORKDIR /build

RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir -r requirements.txt && \
    find /root/.local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type f -name "*.pyc" -delete

# Runtime
FROM python:3.11-alpine

LABEL maintainer="Kor'tana Team" \
      description="Heartbeat Monitoring Service" \
      version="1.0.0"

RUN addgroup -g 1002 heartbeat && \
    adduser -D -u 1002 -G heartbeat heartbeat && \
    apk add --no-cache curl ca-certificates

WORKDIR /app

COPY --from=builder --chown=heartbeat:heartbeat /root/.local /home/heartbeat/.local

ENV PATH=/home/heartbeat/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

COPY --chown=heartbeat:heartbeat . .

USER heartbeat

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/ping || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
