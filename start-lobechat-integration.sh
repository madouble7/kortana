#!/bin/bash
# LobeChat Integration Startup Script
# This script starts both the Kor'tana backend and LobeChat frontend

set -e

echo "================================================"
echo "  Kor'tana + LobeChat Integration Startup"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.template .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys before continuing"
    echo "   Required keys: OPENAI_API_KEY, KORTANA_API_KEY"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo ""
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check backend health
echo ""
echo "🔍 Checking Kor'tana backend health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Kor'tana backend is running on http://localhost:8000"
else
    echo "⚠️  Backend is starting... this may take a moment"
fi

# Check frontend
echo ""
echo "🔍 Checking LobeChat frontend..."
if curl -s http://localhost:3210 > /dev/null 2>&1; then
    echo "✅ LobeChat frontend is running on http://localhost:3210"
else
    echo "⚠️  Frontend is starting... this may take a moment"
fi

echo ""
echo "================================================"
echo "  Services Started Successfully!"
echo "================================================"
echo ""
echo "📍 Access Points:"
echo "   • LobeChat UI:        http://localhost:3210"
echo "   • Kor'tana API:       http://localhost:8000"
echo "   • API Documentation:  http://localhost:8000/docs"
echo ""
echo "📋 Configuration Steps:"
echo "   1. Open LobeChat at http://localhost:3210"
echo "   2. Go to Settings → Language Model"
echo "   3. Add custom provider:"
echo "      - Name: Kor'tana"
echo "      - Base URL: http://localhost:8000/v1"
echo "      - API Key: <from your .env file>"
echo ""
echo "📖 For detailed setup: docs/LOBECHAT_INTEGRATION_GUIDE.md"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs:     docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart:       docker-compose restart"
echo ""
