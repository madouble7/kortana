#!/bin/sh
# Daemon startup script.
# Migrations are handled by the API service on startup.
# The daemon waits for Postgres then starts the worker.
set -e

# Wait for Postgres to be reachable before starting
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "[kortana-daemon] Waiting for Postgres to be ready..."
    MAX_RETRIES=20
    COUNT=0
    until python -c "
import sys, os
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
            echo "[kortana-daemon] Postgres not ready after $MAX_RETRIES attempts, continuing anyway..."
            break
        fi
        echo "[kortana-daemon] Postgres not ready yet (attempt $COUNT/$MAX_RETRIES), waiting 3s..."
        sleep 3
    done
    echo "[kortana-daemon] Postgres is ready."
fi

exec python -m src.kortana.daemon_worker
