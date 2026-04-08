#!/bin/sh
# Daemon startup script.
# Migrations are handled by the API service on startup.
# The daemon waits for Postgres, ensures a writable git workspace, then starts.
set -e

DEFAULT_WORKSPACE_ROOT="/app/tmp/kortana_repo"
PACKAGED_REPO_ROOT="${REPO_ROOT:-/app}"
WORKSPACE_ROOT="${KORTANA_WORKSPACE_ROOT:-$DEFAULT_WORKSPACE_ROOT}"
GIT_REF="${KORTANA_DAEMON_GIT_REF:-${RAILWAY_GIT_BRANCH:-main}}"
GITHUB_OWNER="${GITHUB_OWNER:-madouble7}"
GITHUB_REPO="${GITHUB_REPO:-kortana}"
CLONE_URL="https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git"

prepare_workspace() {
    if [ -d "$PACKAGED_REPO_ROOT/.git" ]; then
        WORKSPACE_ROOT="$PACKAGED_REPO_ROOT"
    elif [ "$WORKSPACE_ROOT" = "$PACKAGED_REPO_ROOT" ] || [ "$WORKSPACE_ROOT" = "/app" ] || [ "$WORKSPACE_ROOT" = "/" ]; then
        WORKSPACE_ROOT="$DEFAULT_WORKSPACE_ROOT"
    fi

    if [ -d "$WORKSPACE_ROOT/.git" ]; then
        echo "[kortana-daemon] Using existing git workspace at $WORKSPACE_ROOT"
        export REPO_ROOT="$WORKSPACE_ROOT"
        export KORTANA_WORKSPACE_ROOT="$WORKSPACE_ROOT"
        return 0
    fi

    if ! command -v git >/dev/null 2>&1; then
        echo "[kortana-daemon] git is not installed; continuing without workspace clone"
        return 0
    fi

    echo "[kortana-daemon] Preparing git workspace at $WORKSPACE_ROOT"
    rm -rf "$WORKSPACE_ROOT"
    mkdir -p "$(dirname "$WORKSPACE_ROOT")"

    if [ -n "$GITHUB_TOKEN" ]; then
        AUTH_HEADER="$(python - <<'PY'
import base64
import os

token = os.environ.get("GITHUB_TOKEN", "")
print(base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("ascii"))
PY
)"
        if git -c "http.extraHeader=Authorization: Basic $AUTH_HEADER" clone --depth 1 --branch "$GIT_REF" "$CLONE_URL" "$WORKSPACE_ROOT"; then
            export REPO_ROOT="$WORKSPACE_ROOT"
            export KORTANA_WORKSPACE_ROOT="$WORKSPACE_ROOT"
            echo "[kortana-daemon] Git workspace ready at $WORKSPACE_ROOT"
            return 0
        fi
        echo "[kortana-daemon] Authenticated clone failed; retrying public clone"
        rm -rf "$WORKSPACE_ROOT"
    fi

    if git clone --depth 1 --branch "$GIT_REF" "$CLONE_URL" "$WORKSPACE_ROOT"; then
        export REPO_ROOT="$WORKSPACE_ROOT"
        export KORTANA_WORKSPACE_ROOT="$WORKSPACE_ROOT"
        echo "[kortana-daemon] Git workspace ready at $WORKSPACE_ROOT"
        return 0
    fi

    echo "[kortana-daemon] Workspace clone failed; continuing with packaged sources"
}

prepare_workspace

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
