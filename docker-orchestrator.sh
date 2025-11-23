#!/bin/bash
# Orion Docker Orchestrator - SEC EDGAR Download
# Manages SEC EDGAR download process using Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed${NC}"
    echo "Please install docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

# Function to build images
build() {
    echo -e "${GREEN}🔨 Building Orion Docker image...${NC}"
    $COMPOSE_CMD build
    echo -e "${GREEN}✅ Build complete${NC}"
}

# Function to download filings
download() {
    local START_YEAR=${1:-2009}
    local END_YEAR=${2:-2010}
    local MAX_WORKERS=${3:-5}
    local SKIP_EXISTING=${4:-true}
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}📥 SEC EDGAR Filing Download${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}   Years: ${START_YEAR} - ${END_YEAR}${NC}"
    echo -e "${YELLOW}   Parallel threads: ${MAX_WORKERS}${NC}"
    echo -e "${YELLOW}   Skip existing: ${SKIP_EXISTING}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Build command arguments
    local CMD_ARGS=(
        "python" "-m" "src.cli" "download"
        "--start-year" "${START_YEAR}"
        "--end-year" "${END_YEAR}"
        "--max-workers" "${MAX_WORKERS}"
    )
    
    if [ "$SKIP_EXISTING" = "false" ]; then
        CMD_ARGS+=("--no-skip-existing")
    fi
    
    $COMPOSE_CMD run --rm download "${CMD_ARGS[@]}" || {
        echo -e "${RED}❌ Download failed${NC}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✅ Download complete${NC}"
    echo -e "${YELLOW}📁 Files saved to: ./Edgar_filings${NC}"
    echo -e "${YELLOW}📋 Metadata saved to: fpi_6k_metadata.csv${NC}"
}

# Function to stop containers
stop() {
    echo -e "${YELLOW}🛑 Stopping containers...${NC}"
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ Containers stopped${NC}"
}

# Function to clean up
clean() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    $COMPOSE_CMD down -v
    docker system prune -f
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Function to show logs
logs() {
    $COMPOSE_CMD logs -f download
}

# Function to show status
status() {
    echo -e "${GREEN}📊 Container Status:${NC}"
    $COMPOSE_CMD ps
}

# Function to show help
show_help() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Orion Docker Orchestrator - SEC EDGAR Download${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  build                    Build Docker image"
    echo "  download [YEAR1] [YEAR2] [WORKERS] [SKIP]  Download SEC filings"
    echo "  stop                     Stop containers"
    echo "  clean                    Clean up Docker resources"
    echo "  logs                     Show download logs"
    echo "  status                   Show container status"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 build"
    echo "  $0 download                    # Default: 2009-2010, 5 workers"
    echo "  $0 download 2020 2021          # Download 2020-2021"
    echo "  $0 download 2009 2010 10        # Use 10 parallel threads"
    echo "  $0 download 2009 2010 5 false  # Re-download existing files"
    echo ""
    echo -e "${YELLOW}Note:${NC} This orchestrator currently handles SEC EDGAR downloads only."
    echo "      Other processes will be added later."
}

# Main command handler
case "$1" in
    build)
        build
        ;;
    download|dl)
        download "$2" "$3" "$4" "$5"
        ;;
    stop)
        stop
        ;;
    clean)
        clean
        ;;
    logs)
        logs
        ;;
    status|ps)
        status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac
