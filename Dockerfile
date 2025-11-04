# Dockerfile for Kor'tana
# Build locally first: npm run build:all
# Then build Docker: docker build -t kortana .

FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies  
RUN npm install --no-audit --no-fund

# Copy application files
COPY dist/ ./dist/
COPY client/build/ ./client/build/

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
