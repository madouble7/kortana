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
