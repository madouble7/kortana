# Multi-stage build for Node.js + TypeScript service with React frontend

# Stage 1: Build React frontend
FROM node:18-alpine AS client-builder

WORKDIR /app/client

# Copy client package files
COPY client/package*.json ./

# Install client dependencies
RUN npm ci --only=production

# Copy client source
COPY client/ ./

# Build React app
RUN npm run build

# Stage 2: Build backend
FROM node:18-alpine AS backend-builder

WORKDIR /app

# Copy root package files
COPY package*.json ./
COPY tsconfig.json ./

# Install backend dependencies
RUN npm ci --only=production

# Copy backend source
COPY src/ ./src/

# Build TypeScript backend
RUN npm run build

# Stage 3: Production image
FROM node:18-alpine

WORKDIR /app

# Copy backend dependencies and built files
COPY --from=backend-builder /app/node_modules ./node_modules
COPY --from=backend-builder /app/dist ./dist
COPY --from=backend-builder /app/package*.json ./

# Copy built React frontend
COPY --from=client-builder /app/client/build ./client/build

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
