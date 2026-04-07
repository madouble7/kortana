#!/bin/bash
# ============================================
# Docker Build Script
# ============================================
# Build all Docker images with proper tagging

set -e

VERSION=${VERSION:-"1.0.0"}
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

echo "Building Kor'tana Docker images..."
echo "Version: $VERSION"
echo "Build Date: $BUILD_DATE"

# Build backend
echo "Building backend..."
docker build \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VERSION="$VERSION" \
  -t kortana/backend:$VERSION \
  -t kortana/backend:latest \
  -f kortana/backend/Dockerfile \
  kortana/backend

# Build frontend
echo "Building frontend..."
docker build \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VERSION="$VERSION" \
  -t kortana/frontend:$VERSION \
  -t kortana/frontend:latest \
  -f kortana/frontend/Dockerfile \
  kortana/frontend

# Build utilities
echo "Building background-agent..."
docker build \
  -t kortana/background-agent:$VERSION \
  -t kortana/background-agent:latest \
  -f utilities/background-agent/Dockerfile \
  utilities/background-agent

echo "Building heartbeat-service..."
docker build \
  -t kortana/heartbeat-service:$VERSION \
  -t kortana/heartbeat-service:latest \
  -f utilities/heartbeat-service/Dockerfile \
  utilities/heartbeat-service

echo "Building hub-dispatcher..."
docker build \
  -t kortana/hub-dispatcher:$VERSION \
  -t kortana/hub-dispatcher:latest \
  -f utilities/hub-dispatcher/Dockerfile \
  utilities/hub-dispatcher

echo "Build complete!"
docker images | grep kortana
