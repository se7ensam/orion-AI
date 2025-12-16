# Distributed Worker System for Parallel Processing

## Overview

The distributed worker system allows you to process EDGAR filings in parallel across multiple Docker containers. This significantly speeds up processing, especially when using AI extraction.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Coordinator                           │
│  - Creates work queue from filings                      │
│  - Monitors worker progress                              │
│  - Collects results                                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Work Queue   │
            │  (File-based) │
            └───────┬───────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌───────┐   ┌───────┐   ┌───────┐
    │Worker1│   │Worker2│   │WorkerN│
    └───┬───┘   └───┬───┘   └───┬───┘
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
            ┌───────────────┐
            │    Neo4j       │
            │  (Shared DB)   │
            └───────────────┘
```

## Quick Start

### 1. Start Infrastructure

```bash
# Start Neo4j and Ollama
docker-compose up -d neo4j ollama

# Wait for Ollama to pull model (first time only)
docker-compose logs -f ollama
```

### 2. Start Workers

```bash
# Start 2 workers (default)
docker-compose up -d worker

# Or scale to more workers
docker-compose up -d --scale worker=4
```

### 3. Run Coordinator

```bash
# Option 1: Run coordinator via Docker
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --year 2010 \
  --limit 10 \
  --wait

# Option 2: Run coordinator locally (if you have Python env)
python -m src.services.coordinator --year 2010 --limit 10 --wait
```

## Scaling Workers

### Scale Up

```bash
# Scale to 4 workers
docker-compose up -d --scale worker=4

# Scale to 8 workers
docker-compose up -d --scale worker=8
```

### Scale Down

```bash
# Scale to 1 worker
docker-compose up -d --scale worker=1

# Stop all workers
docker-compose stop worker
```

## How It Works

### 1. Coordinator Creates Jobs

The coordinator:
- Scans for filings based on year/limit filters
- Creates JSON job files in `data/queue/pending/`
- Each job contains filing path and processing options

### 2. Workers Process Jobs

Each worker:
- Polls the `pending/` directory for jobs
- Moves job to `processing/` when picked up
- Processes the filing (AI extraction + Neo4j insertion)
- Moves job to `completed/` or `failed/` when done

### 3. Coordinator Monitors Progress

The coordinator:
- Tracks pending/processing/completed/failed counts
- Shows real-time progress
- Collects final statistics

## File-Based Queue Structure

```
data/queue/
├── pending/      # Jobs waiting to be processed
├── processing/   # Jobs currently being processed
├── completed/    # Successfully completed jobs
└── failed/       # Failed jobs (with error info)
```

## Performance

### Sequential Processing (Single Process)
- 10 filings: ~33 seconds
- 100 filings: ~330 seconds (5.5 minutes)

### Distributed Processing (2 Workers)
- 10 filings: ~16-17 seconds (2x faster)
- 100 filings: ~165 seconds (2.5 minutes, 2x faster)

### Distributed Processing (4 Workers)
- 10 filings: ~8-9 seconds (4x faster)
- 100 filings: ~82 seconds (1.4 minutes, 4x faster)

## Usage Examples

### Basic Usage

```bash
# 1. Start workers
docker-compose up -d --scale worker=2

# 2. Run coordinator
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --year 2010 \
  --limit 10 \
  --wait
```

### Process All Filings for a Year

```bash
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --year 2009 \
  --wait
```

### Disable AI Extraction

```bash
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --year 2010 \
  --limit 10 \
  --no-ai \
  --wait
```

### Monitor Workers

```bash
# View worker logs
docker-compose logs -f worker

# View specific worker
docker-compose logs -f worker_1

# Check worker status
docker-compose ps worker
```

## Environment Variables

### Worker Environment

- `WORKER_ID`: Unique identifier (auto-generated from HOSTNAME)
- `QUEUE_DIR`: Queue directory path (default: `/app/data/queue`)
- `OLLAMA_BASE_URL`: Ollama service URL (default: `http://ollama:11434`)
- `USE_AI_EXTRACTION`: Enable/disable AI (default: `true`)

### Coordinator Environment

- `QUEUE_DIR`: Queue directory path (default: `/app/data/queue`)

## Troubleshooting

### Workers Not Processing

1. Check if workers are running:
   ```bash
   docker-compose ps worker
   ```

2. Check worker logs:
   ```bash
   docker-compose logs worker
   ```

3. Verify Neo4j connection:
   ```bash
   docker-compose exec worker python -m src.cli test-db --neo4j
   ```

### Ollama Connection Issues

1. Check if Ollama is running:
   ```bash
   docker-compose ps ollama
   ```

2. Check Ollama logs:
   ```bash
   docker-compose logs ollama
   ```

3. Test Ollama from worker:
   ```bash
   docker-compose exec worker curl http://ollama:11434/api/tags
   ```

### Jobs Stuck in Processing

If jobs are stuck in `processing/` directory (worker crashed):

1. Check for crashed workers:
   ```bash
   docker-compose ps worker
   ```

2. Manually move stuck jobs back to pending:
   ```bash
   # This would need a cleanup script
   mv data/queue/processing/*.json data/queue/pending/
   ```

## Advanced Usage

### Custom Queue Directory

```bash
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --queue-dir /custom/path/queue \
  --year 2010 \
  --wait
```

### Run Coordinator Without Waiting

```bash
# Create jobs and exit (workers process in background)
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --year 2010 \
  --limit 100

# Check status later
docker-compose run --rm coordinator \
  python -m services.coordinator.main \
  --wait
```

## Integration with CLI

You can also use the CLI with distributed mode:

```bash
# Local CLI with distributed mode
python -m src.cli load-graph --year 2010 --limit 10 --distributed
```

This will:
1. Create the work queue
2. Wait for workers to process
3. Show final results

## Best Practices

1. **Start with Few Workers**: Test with 2 workers first, then scale up
2. **Monitor Resources**: Each worker uses CPU/RAM for AI extraction
3. **Check Neo4j Capacity**: Ensure Neo4j can handle concurrent writes
4. **Use Health Checks**: Monitor worker health with `docker-compose ps`
5. **Clean Queue**: Clear old queue files before new runs

## Cleanup

```bash
# Stop all workers
docker-compose stop worker

# Remove queue files
rm -rf data/queue/*

# Remove all containers
docker-compose down
```

