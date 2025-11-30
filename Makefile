# Orion Makefile - Docker Orchestration

.PHONY: help build download neo4j neo4j-stop neo4j-logs stop clean logs status

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
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make neo4j"
	@echo "  make download"
	@echo "  docker-compose run --rm download python -m src.cli download --start-year 2020 --end-year 2021"

# Build Docker image
build:
	docker-compose build

# Download filings (default: 2009-2010, 5 workers)
download:
	docker-compose run --rm download python -m src.cli download --start-year 2009 --end-year 2010 --max-workers 5

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
