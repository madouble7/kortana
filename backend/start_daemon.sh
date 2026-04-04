#!/bin/sh
# Daemon startup script with graceful migration handling.
# Alembic can fail with "table already exists" when the DB was previously
# initialized via create_all but not tracked by alembic. In that case,
# stamp the current head and continue rather than hard-crashing.

set -e

echo "[kortana-daemon] Running database migrations..."
if alembic upgrade head; then
    echo "[kortana-daemon] Migrations complete."
else
    echo "[kortana-daemon] Migration failed — tables may already exist. Stamping to current head..."
    alembic stamp head
    echo "[kortana-daemon] DB stamped. Verifying..."
    alembic upgrade head
    echo "[kortana-daemon] Verified clean."
fi

echo "[kortana-daemon] Starting daemon worker..."
exec python -m src.kortana.daemon_worker
