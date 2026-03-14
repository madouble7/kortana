# Dockerfile for Kor'tana
# Build locally first: npm run build:all or ./build.sh
# Then build Docker: docker build -t kortana .
# Note: This Dockerfile expects pre-built artifacts in dist/ and client/build/
# If these directories don't exist, the build will fail

FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies  
RUN npm install --no-audit --no-fund

# Copy application files
# These directories must exist before building the Docker image
COPY dist/ ./dist/
COPY client/build/ ./client/build/

# Verify required files exist
RUN test -f dist/server.js || (echo "Error: dist/server.js not found. Run 'npm run build:all' first." && exit 1)
RUN test -f client/build/index.html || (echo "Error: client/build/index.html not found. Run 'npm run build:all' first." && exit 1)

# Set environment
ENV NODE_ENV=production
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Run the application
CMD ["node", "dist/server.js"]
# Multi-stage build for Kor'tana Unified Platform

# --- Stage 1: Frontend Build ---
FROM node:20-slim as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Stage 2: Backend Builder ---
FROM python:3.11-slim as backend-builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 3: Final Production Image ---
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend application code
COPY backend/ .

# Copy built frontend assets to backend static directory
COPY --from=frontend-builder /app/frontend/dist ./static

# Environment variables
ENV PORT=8000
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "src.kortana.main:app", "--host", "0.0.0.0", "--port", "8000"]
