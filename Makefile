# Orion Makefile - Docker Orchestration

.PHONY: help build download neo4j neo4j-stop neo4j-logs stop clean logs status workers workers-scale workers-logs coordinator

# Default target
help:
	@echo "Orion Docker Orchestration"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build Docker image"
	@echo "  make download       - Download SEC filings (2009-2010, 5 workers)"
	@echo "  make neo4j          - Start Neo4j database"
	@echo "  make neo4j-stop     - Stop Neo4j database"
	@echo "  make neo4j-logs     - Show Neo4j logs"
	@echo "  make stop           - Stop all containers"
	@echo "  make clean          - Clean up Docker resources"
	@echo "  make logs           - Show download logs"
	@echo "  make status         - Show container status"
	@echo "  make workers        - Start worker services (2 workers)"
	@echo "  make workers-scale  - Scale workers (e.g., make workers-scale N=4)"
	@echo "  make workers-logs   - Show worker logs"
	@echo "  make coordinator    - Run coordinator to process filings"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make neo4j"
	@echo "  make download"
	@echo "  make workers"
	@echo "  make coordinator YEAR=2010 LIMIT=10"
	@echo "  docker-compose run --rm download python -m services.cli.main download --start-year 2020 --end-year 2021"

# Build Docker image
build:
	docker-compose build

# Download filings (default: 2009-2010)
download:
	docker-compose run --rm download python -m services.cli.main download --start-year 2009 --end-year 2010

# Start Neo4j
neo4j:
	docker-compose up -d neo4j
	@echo ""
	@echo "✓ Neo4j started!"
	@echo "  Browser: http://localhost:7474"
	@echo "  Bolt: bolt://localhost:7687"
	@echo "  Username: neo4j"
	@echo "  Password: orion123 (or check .env)"

# Stop Neo4j
neo4j-stop:
	docker-compose stop neo4j

# Show Neo4j logs
neo4j-logs:
	docker-compose logs -f neo4j

# Start Ollama
ollama:
	docker-compose up -d ollama
	@echo ""
	@echo "✓ Ollama started!"
	@echo "  API: http://localhost:11434"
	@echo "  Waiting for model download..."

# Start Workers
workers:
	docker-compose up -d --scale worker=2 worker
	@echo ""
	@echo "✓ Workers started (2 workers)"
	@echo "  Scale up: make workers-scale N=4"
	@echo "  View logs: make workers-logs"

# Scale Workers
workers-scale:
	@if [ -z "$(N)" ]; then \
		echo "Usage: make workers-scale N=4"; \
		exit 1; \
	fi
	docker-compose up -d --scale worker=$(N) worker
	@echo ""
	@echo "✓ Scaled workers to $(N)"

# Show Worker Logs
workers-logs:
	docker-compose logs -f worker

# Run Coordinator
coordinator:
	@YEAR=$(or $(YEAR),); \
	LIMIT=$(or $(LIMIT),); \
	NO_AI=$(or $(NO_AI),); \
	ARGS=""; \
	if [ -n "$$YEAR" ]; then ARGS="$$ARGS --year $$YEAR"; fi; \
	if [ -n "$$LIMIT" ]; then ARGS="$$ARGS --limit $$LIMIT"; fi; \
	if [ -n "$$NO_AI" ]; then ARGS="$$ARGS --no-ai"; fi; \
	docker-compose run --rm coordinator python -m services.coordinator.main $$ARGS --wait

# Stop containers
stop:
	docker-compose down

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Show logs
logs:
	docker-compose logs -f download

# Show status
status:
	docker-compose ps
