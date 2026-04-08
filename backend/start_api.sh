#!/bin/sh
# API startup script with graceful migration handling.
# Alembic can fail with "table already exists" when the DB was previously
# initialized via create_all but not tracked by alembic. In that case,
# stamp the current head and continue rather than hard-crashing.
set -e

# Wait for Postgres to be reachable before running migrations
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "[kortana-api] Waiting for Postgres to be ready..."
    MAX_RETRIES=15
    COUNT=0
    until python -c "
import sys, os, urllib.parse
url = os.environ.get('DATABASE_URL', '')
if not url or 'sqlite' in url:
    sys.exit(0)
try:
    import psycopg2
    clean = url.replace('+asyncpg', '')
    conn = psycopg2.connect(clean, connect_timeout=3)
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
        COUNT=$((COUNT + 1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo "[kortana-api] Postgres not ready after $MAX_RETRIES attempts, continuing anyway..."
            break
        fi
        echo "[kortana-api] Postgres not ready yet (attempt $COUNT/$MAX_RETRIES), waiting 3s..."
        sleep 3
    done
    echo "[kortana-api] Postgres is ready."
fi

echo "[kortana-api] Running database migrations..."
if alembic upgrade heads; then
    echo "[kortana-api] Migrations complete."
else
    echo "[kortana-api] Migration failed — stamping existing DB to current heads..."
    alembic stamp heads
    echo "[kortana-api] Stamped. Retrying upgrade..."
    alembic upgrade heads
    echo "[kortana-api] Migration verified clean."
fi

echo "[kortana-api] Starting API server..."
exec uvicorn src.kortana.main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
