#!/bin/bash
# Build script for Kor'tana

set -e

echo "🏗️  Building Kor'tana..."

# Build backend
echo "📦 Building backend..."
npm run build

# Build frontend  
echo "⚛️  Building frontend..."
npm run client:build

echo "✅ Build complete!"
echo "📁 Backend: dist/"
echo "📁 Frontend: client/build/"
echo ""
echo "To run locally: npm start"
echo "To build Docker: docker build -t kortana ."
