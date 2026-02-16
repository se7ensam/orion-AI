.PHONY: help install build clean test docker-up docker-down docker-logs worker-start verify status

# Default target
help:
	@echo "Orion Backend - Available Commands:"
	@echo ""
	@echo "  make install       - Install all dependencies"
	@echo "  make build         - Build all services"
	@echo "  make build-clean   - Clean and rebuild"
	@echo "  make clean         - Remove build artifacts"
	@echo ""
	@echo "  make docker-up     - Start Docker stack"
	@echo "  make docker-down   - Stop Docker stack"
	@echo "  make docker-logs   - Follow worker logs"
	@echo "  make docker-build  - Build Docker images"
	@echo ""
	@echo "  make worker-start  - Start ingestion worker"
	@echo "  make worker-build  - Build worker only"
	@echo ""
	@echo "  make migrate       - Run database migrations"
	@echo "  make verify        - Verify optimizations"
	@echo "  make status        - Check system status"
	@echo ""
	@echo "  make seed-fetch    - Fetch SEC master index"
	@echo "  make seed-filter   - Filter 6-K filings"
	@echo "  make seed-push     - Push jobs to queue"
	@echo "  make seed-purge    - Purge queue (with confirmation)"
	@echo ""

# Installation
install:
	@echo "Installing dependencies..."
	npm install

# Building
build:
	@echo "Building all services..."
	npm run build

build-clean:
	@echo "Clean building all services..."
	npm run build:clean

worker-build:
	@echo "Building worker service..."
	npm run worker:build

# Cleaning
clean:
	@echo "Removing build artifacts..."
	find . -name 'dist' -type d -not -path './node_modules/*' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.tsbuildinfo' -type f -not -path './node_modules/*' -delete 2>/dev/null || true
	@echo "Clean complete"

deep-clean: clean
	@echo "Removing node_modules..."
	npm run clean

# Docker operations
docker-up:
	@echo "Starting Docker stack..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	sleep 5
	docker-compose ps

docker-down:
	@echo "Stopping Docker stack..."
	docker-compose down

docker-logs:
	@echo "Following worker logs (Ctrl+C to exit)..."
	docker-compose logs -f ingestion-worker

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-restart:
	@echo "Restarting worker..."
	docker-compose restart ingestion-worker
	@echo "Waiting for restart..."
	sleep 3
	docker-compose logs --tail=50 ingestion-worker

# Worker operations
worker-start:
	@echo "Starting worker..."
	npm run worker:start

# Database operations
migrate:
	@echo "Running migrations..."
	cd scripts && npx tsx run-migrations.ts

# Monitoring and verification
verify:
	@echo "Verifying optimizations..."
	cd scripts && npx tsx verify-optimizations.ts

status:
	@echo "Checking system status..."
	cd scripts && npx tsx check-status.ts

# Queue seeding
seed-fetch:
	@echo "Fetching SEC master index..."
	cd scripts/seed-queue && npx tsx fetch-master-idx.ts

seed-filter:
	@echo "Filtering 6-K filings..."
	cd scripts/seed-queue && npx tsx filter-filings.ts

seed-push:
	@echo "Pushing jobs to queue..."
	cd scripts/seed-queue && npx tsx push-to-queue.ts

seed-purge:
	@echo "Purging queue..."
	cd scripts/seed-queue && npx tsx purge-queue.ts

seed-all: seed-fetch seed-filter seed-push
	@echo "Seeding complete!"

# Development
dev: docker-up
	@echo "Starting development environment..."
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - RabbitMQ: localhost:5672"
	@echo "  - RabbitMQ Management: http://localhost:15672"
	@echo ""
	@echo "Run 'make worker-start' to start the worker"

# Production deployment
deploy: build docker-build
	@echo "Deployment build complete"
	@echo "Images ready to push to registry"

# Quick start
quickstart: install build migrate seed-fetch seed-filter
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Start infrastructure: make docker-up"
	@echo "  2. Push jobs to queue:   make seed-push"
	@echo "  3. Start worker:         make worker-start"
	@echo "  4. Check status:         make status"
	@echo ""
