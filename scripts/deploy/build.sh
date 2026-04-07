#!/bin/bash
# Build script for Kor'tana

set -e

echo "🏗️  Building Kor'tana..."

# Build backend
echo "📦 Building backend..."
npm run build

# Verify backend build
if [ ! -d "dist" ] || [ ! -f "dist/server.js" ]; then
  echo "❌ Backend build failed: dist/server.js not found"
  exit 1
fi

# Build frontend  
echo "⚛️  Building frontend..."
npm run client:build

# Verify frontend build
if [ ! -d "client/build" ] || [ ! -f "client/build/index.html" ]; then
  echo "❌ Frontend build failed: client/build/index.html not found"
  exit 1
fi

echo "✅ Build complete!"
echo "📁 Backend: dist/"
echo "📁 Frontend: client/build/"
echo ""
echo "To run locally: npm start"
echo "To build Docker: docker build -t kortana ."
