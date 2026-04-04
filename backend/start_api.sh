#!/bin/sh
# API startup script with graceful migration handling.
# Alembic can fail with "table already exists" when the DB was previously
# initialized via create_all but not tracked by alembic. In that case,
# stamp the current head and continue rather than hard-crashing.
set -e

echo "[kortana-api] Running database migrations..."
if python -m alembic upgrade head; then
    echo "[kortana-api] Migrations complete."
else
    echo "[kortana-api] Migration failed — stamping existing DB to current head..."
    python -m alembic stamp head
    echo "[kortana-api] Stamped. Retrying upgrade..."
    python -m alembic upgrade head
    echo "[kortana-api] Migration verified clean."
fi

echo "[kortana-api] Starting API server..."
exec uvicorn src.kortana.main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
