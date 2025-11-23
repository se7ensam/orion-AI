# Orion Makefile - Docker Orchestration for SEC EDGAR Download

.PHONY: help build download stop clean logs status

# Default target
help:
	@echo "Orion Docker Orchestration - SEC EDGAR Download"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build Docker image"
	@echo "  make download       - Download SEC filings (2009-2010, 5 workers)"
	@echo "  make stop           - Stop containers"
	@echo "  make clean           - Clean up Docker resources"
	@echo "  make logs            - Show download logs"
	@echo "  make status          - Show container status"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make download"
	@echo "  docker-compose run --rm download python -m src.cli download --start-year 2020 --end-year 2021"

# Build Docker image
build:
	docker-compose build

# Download filings (default: 2009-2010, 5 workers)
download:
	docker-compose run --rm download python -m src.cli download --start-year 2009 --end-year 2010 --max-workers 5

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
