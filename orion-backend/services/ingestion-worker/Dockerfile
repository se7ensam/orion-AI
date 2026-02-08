# Multi-stage build for optimized production image

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY ../../shared/package*.json ../../shared/
COPY ../../tsconfig.base.json ../../

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .
COPY ../../shared/ ../../shared/

# Build TypeScript
RUN npm run build

# Stage 2: Production
FROM node:20-alpine

# Add metadata
LABEL maintainer="Orion Team"
LABEL description="SEC Filings Ingestion Worker"
LABEL version="2.0"

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy package files and install production dependencies only
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built artifacts from builder
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/../../shared/dist ../../shared/dist

# Switch to non-root user
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "process.exit(0)" || exit 1

# Graceful shutdown support
STOPSIGNAL SIGTERM

# Start the worker
CMD ["node", "dist/index.js"]
