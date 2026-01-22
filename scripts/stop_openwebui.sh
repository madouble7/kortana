#!/bin/bash
# Stop Kor'tana with Open WebUI

echo "🛑 Stopping Open WebUI and Kor'tana..."

# Stop Docker containers
docker compose -f docker-compose.openwebui.yml down

# Find and stop backend
BACKEND_PID=$(ps aux | grep "uvicorn src.kortana.main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$BACKEND_PID" ]; then
    echo "🛑 Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID
fi

echo "✅ All services stopped"
