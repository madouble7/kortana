# ============================================
# Kor'tana Frontend - Production Dockerfile
# ============================================
# Multi-stage build for optimized React frontend

# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production Runtime with Nginx
FROM nginx:alpine

# Set labels
LABEL maintainer="Kor'tana Team"
LABEL description="Kor'tana Frontend UI Service"
LABEL version="1.0.0"

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /build/build /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1000 kortana && \
    adduser -D -u 1000 -G kortana kortana && \
    chown -R kortana:kortana /usr/share/nginx/html && \
    chown -R kortana:kortana /var/cache/nginx && \
    chown -R kortana:kortana /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown kortana:kortana /var/run/nginx.pid

# Switch to non-root user
USER kortana

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
