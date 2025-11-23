# Docker Orchestration Guide - SEC EDGAR Download

## Overview

Orion uses Docker containers to orchestrate the SEC EDGAR download process. The download service runs in a separate container, making it easy to manage and deploy.

**Note:** Currently, only the SEC EDGAR download process is containerized. Other processes (database setup, etc.) will be added later.

## Quick Start

### 1. Build Docker Image

```bash
./docker-orchestrator.sh build
# OR
make build
# OR
docker-compose build
```

### 2. Download SEC Filings

```bash
# Default: 2009-2010, 5 workers
./docker-orchestrator.sh download

# Custom years and workers
./docker-orchestrator.sh download 2020 2021 10

# Re-download existing files
./docker-orchestrator.sh download 2009 2010 5 false
```

### 3. View Logs

```bash
./docker-orchestrator.sh logs
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Orchestrator             │
│      (docker-orchestrator.sh)            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
            ┌─────────┐
            │ Download│
            │ Container│
            └─────────┘
                  │
                  ▼
            SEC EDGAR API
```

## Services

### Download Service

Downloads SEC EDGAR 6-K filings for Foreign Private Issuers.

**Usage:**
```bash
./docker-orchestrator.sh download [START_YEAR] [END_YEAR] [MAX_WORKERS] [SKIP_EXISTING]
```

**Parameters:**
- `START_YEAR` - Starting year (default: 2009)
- `END_YEAR` - Ending year (default: 2010)
- `MAX_WORKERS` - Number of parallel threads (default: 5)
- `SKIP_EXISTING` - Skip existing files (default: true, set to "false" to re-download)

**Examples:**
```bash
# Default download
./docker-orchestrator.sh download

# Download 2020-2021 with 10 workers
./docker-orchestrator.sh download 2020 2021 10

# Re-download existing files
./docker-orchestrator.sh download 2009 2010 5 false
```

**Direct Docker Compose:**
```bash
docker-compose run --rm download \
  python -m src.cli download \
  --start-year 2009 \
  --end-year 2010 \
  --max-workers 5
```

## Volume Mounts

Data is persisted through Docker volume mounts:

- `./Edgar_filings` → Downloaded filing files
- `./metadata` → SEC company index files
- `./fpi_list.csv` → List of FPIs
- `./fpi_6k_metadata.csv` → Filing metadata

## Environment Variables

The download service reads from `.env` file (mounted as read-only):

```bash
# SEC EDGAR uses User-Agent from code (no env var needed)
# Other settings can be added here if needed
```

## Common Workflows

### Initial Setup
```bash
# 1. Build image
./docker-orchestrator.sh build

# 2. Download filings
./docker-orchestrator.sh download
```

### Download Different Years
```bash
# Download 2020-2021
./docker-orchestrator.sh download 2020 2021

# Download with more workers
./docker-orchestrator.sh download 2020 2021 10
```

### View Progress
```bash
# Watch logs in real-time
./docker-orchestrator.sh logs
```

### Check Status
```bash
./docker-orchestrator.sh status
```

### Cleanup
```bash
# Stop containers
./docker-orchestrator.sh stop

# Clean up everything
./docker-orchestrator.sh clean
```

## Direct Docker Compose Commands

You can also use `docker-compose` directly:

```bash
# Build
docker-compose build

# Run download
docker-compose run --rm download python -m src.cli download --start-year 2009 --end-year 2010

# View logs
docker-compose logs -f download

# Stop
docker-compose down
```

## Using Make

Alternative interface using Make:

```bash
make build
make download
make logs
make status
make stop
make clean
```

## Features

- ✅ **Isolated Environment**: Download runs in isolated container
- ✅ **Data Persistence**: Files saved to mounted volumes
- ✅ **Parallel Downloads**: Configurable thread count
- ✅ **Rate Limiting**: SEC-compliant (10 requests/second)
- ✅ **Resume Capability**: Skips already downloaded files
- ✅ **Progress Tracking**: Real-time progress bars

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs download

# Check status
docker-compose ps
```

### Permission issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./Edgar_filings ./metadata
```

### Rebuild after code changes
```bash
./docker-orchestrator.sh build
```

### View container shell
```bash
docker-compose run --rm download /bin/bash
```

## Future Additions

The following processes will be added to Docker orchestration later:
- Database setup service
- Database test service
- Neo4j database container
- Document processing service
- LLM integration service

## Notes

- The download service doesn't require Neo4j or other databases
- All downloads are saved to `./Edgar_filings/` directory
- Metadata is saved to CSV files in the project root
- The container uses the same rate limiting as local execution
