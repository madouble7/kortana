#!/bin/bash
# Quick start script for Kor'tana with Open WebUI

set -e

echo "🚀 Starting Kor'tana with Open WebUI..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.template .env
    echo "📝 Please edit .env file with your API keys before continuing."
    exit 1
fi

# Start Kor'tana backend
echo "🔧 Starting Kor'tana backend..."
python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Open WebUI
echo "🌐 Starting Open WebUI..."
docker compose -f docker-compose.openwebui.yml up -d

echo ""
echo "✨ Kor'tana with Open WebUI is ready!"
echo ""
echo "🔗 Open WebUI:    http://localhost:3000"
echo "🔗 API Docs:      http://localhost:8000/docs"
echo "🔗 Health Check:  http://localhost:8000/health"
echo ""
echo "📚 Documentation: docs/OPENWEBUI_INTEGRATION.md"
echo ""
echo "To stop all services, run: ./scripts/stop_openwebui.sh"
