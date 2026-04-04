#!/bin/sh
# Daemon startup script.
# Migrations are handled by the API service on startup.
# The daemon just needs to run the worker process.
set -e
exec python -m src.kortana.daemon_worker
