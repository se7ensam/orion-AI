FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
COPY tsconfig.base.json ./
COPY services/ingestion-worker ./services/ingestion-worker
COPY shared ./shared

# Clean install including workspaces
RUN npm install

# Build
WORKDIR /app/services/ingestion-worker
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/services/ingestion-worker/dist ./services/ingestion-worker/dist
COPY --from=builder /app/services/ingestion-worker/package.json ./services/ingestion-worker/
# Also need shared dist
COPY --from=builder /app/shared/dist ./shared/dist
COPY --from=builder /app/shared/package.json ./shared/

WORKDIR /app/services/ingestion-worker

CMD ["npm", "start"]
