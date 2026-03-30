#!/bin/bash
# ============================================
# Docker Deployment Script
# ============================================
# Deploy Kor'tana using Docker Compose

set -e

ENVIRONMENT=${1:-"development"}

echo "Deploying Kor'tana - Environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Using production configuration..."
    docker-compose -f docker-compose.prod.yml up -d
elif [ "$ENVIRONMENT" = "development" ]; then
    echo "Using development configuration..."
    docker-compose up -d
else
    echo "Invalid environment: $ENVIRONMENT"
    echo "Usage: ./deploy.sh [development|production]"
    exit 1
fi

echo "Waiting for services to be healthy..."
sleep 10

echo "Checking service status..."
docker-compose ps

echo "Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "  Prometheus: http://localhost:9090 (with --profile monitoring)"
    echo "  Grafana: http://localhost:3001 (with --profile monitoring)"
fi
