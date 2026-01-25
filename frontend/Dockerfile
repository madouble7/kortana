# ============================================
# Kor'tana Frontend - Production Dockerfile
# ============================================
# Multi-stage build for optimized React frontend

# Stage 1: Builder
FROM node:20-alpine AS builder

# Install security updates
RUN apk upgrade --no-cache

WORKDIR /build

# Copy package files first for better caching
COPY package*.json ./

# Install ALL dependencies (including devDependencies needed for build)
RUN --mount=type=cache,target=/root/.npm \
    npm ci && \
    npm cache clean --force

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production Runtime with Nginx
FROM nginx:1.25-alpine

# Install security updates
RUN apk upgrade --no-cache && \
    apk add --no-cache wget

# Set labels
LABEL maintainer="Kor'tana Team"
LABEL description="Kor'tana Frontend UI Service"
LABEL version="1.0.0"

# Remove default nginx config and www data
RUN rm -rf /etc/nginx/conf.d/default.conf \
    /usr/share/nginx/html/*

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /build/build /usr/share/nginx/html

# Create non-root user and set permissions
RUN addgroup -g 1000 kortana && \
    adduser -D -u 1000 -G kortana kortana && \
    chown -R kortana:kortana /usr/share/nginx/html && \
    chown -R kortana:kortana /var/cache/nginx && \
    chown -R kortana:kortana /var/log/nginx && \
    mkdir -p /var/run && \
    touch /var/run/nginx.pid && \
    chown kortana:kortana /var/run/nginx.pid && \
    chmod 755 /usr/share/nginx/html

# Switch to non-root user
USER kortana

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
