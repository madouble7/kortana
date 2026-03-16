# ============================================
# Kor'tana Frontend - Production Dockerfile
# ============================================
# Multi-stage build for optimized React frontend with Nginx

# Stage 1: Builder
FROM node:20-alpine AS builder

# Install security updates
RUN apk upgrade --no-cache && \
    apk add --no-cache python3 make g++

WORKDIR /build

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with npm ci (for reproducibility) and aggressive caching
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit && \
    npm cache clean --force

# Copy source code
COPY . .

# Build the application with production optimizations
RUN NODE_ENV=production npm run build && \
    rm -rf node_modules .npm src tests public *.config.* .babelrc* .env* && \
    find /build -type f -name "*.map" -delete

# Stage 2: Production Runtime with optimized Nginx
FROM nginx:1.25.5-alpine

# Install security updates
RUN apk upgrade --no-cache && \
    apk add --no-cache wget curl ca-certificates

# Set labels
LABEL maintainer="Kor'tana Team" \
      description="Kor'tana Frontend UI Service" \
      version="1.0.0"

# Remove default nginx config and www data
RUN rm -rf /etc/nginx/conf.d/default.conf \
           /usr/share/nginx/html/* \
           /var/cache/nginx/* \
           /var/run/*.pid

# Create optimized nginx config with security headers and caching
RUN mkdir -p /etc/nginx/conf.d && cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 3000 default_server;
    listen [::]:3000 default_server;
    server_name _;

    root /usr/share/nginx/html;
    index index.html index.htm;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Performance optimizations
    gzip on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json image/svg+xml;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # HTML with conditional caching
    location ~* \.html?$ {
        expires 0;
        add_header Cache-Control "public, max-age=0, must-revalidate";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
        expires 0;
        add_header Cache-Control "public, max-age=0, must-revalidate";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
    }
}
EOF

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
    chmod 755 /usr/share/nginx/html && \
    chmod 755 /var/cache/nginx

# Nginx tuning for performance
RUN cat >> /etc/nginx/nginx.conf << 'EOF'

# Performance tuning
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
sendfile on;
tcp_nopush on;
tcp_nodelay on;
types_hash_max_size 2048;
client_max_body_size 20M;
EOF

# Switch to non-root user
USER kortana

# Expose port
EXPOSE 3000

# Health check with proper endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
