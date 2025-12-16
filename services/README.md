# Orion Services

This directory contains all microservices for the Orion project, following a microservices architecture.

## Structure

```
services/
├── cli/                  # CLI Service (Python) - Main entry point
│   ├── cli.py           # Command-line interface
│   ├── main.py          # Service entry point
│   └── __init__.py
│
├── database/             # Database Service (Python)
│   ├── neo4j_connection.py    # Neo4j connection and schema
│   ├── oracle_connection.py   # Oracle AI Vector DB connection
│   └── __init__.py
│
├── data_loader/         # Data Loader Service (Python)
│   ├── data_loader.py   # Loads and parses EDGAR filings
│   └── __init__.py
│
├── graph_builder/       # Graph Builder Service (Python)
│   ├── graph_builder.py # Extracts entities and builds Neo4j graph
│   └── __init__.py
│
├── downloader/          # Downloader Service (TypeScript)
│   ├── src/            # TypeScript source files
│   ├── dist/           # Compiled JavaScript (generated)
│   ├── package.json    # Service dependencies
│   └── tsconfig.json   # TypeScript configuration
│
├── ai/                  # AI Services (Python)
│   ├── ai_analyzer.py  # AI-powered code analysis
│   ├── ai_extractor.py # AI entity extraction
│   ├── cypher_rag.py   # Natural language to Cypher queries
│   └── __init__.py
│
├── coordinator/         # Coordinator Service (Python)
│   ├── coordinator.py  # Work queue management
│   ├── main.py         # Service entry point
│   └── __init__.py
│
├── worker/             # Worker Service (Python)
│   ├── worker.py        # Distributed filing processor
│   ├── main.py         # Service entry point
│   └── __init__.py
│
└── README.md           # This file
```

## Services

### CLI Service (Python)

**Location:** `services/cli/`

**Purpose:** Main command-line interface for all Orion operations.

**Usage:**
```bash
python -m services.cli.main download --start-year 2009 --end-year 2010
python -m services.cli.main setup-db
python -m services.cli.main load-graph --year 2009
python -m services.cli.main query "Find all companies"
```

### Database Service (Python)

**Location:** `services/database/`

**Purpose:** Database connection management for Neo4j and Oracle AI Vector DB.

**Components:**
- `neo4j_connection.py` - Neo4j connection, schema setup, queries
- `oracle_connection.py` - Oracle AI Vector DB connection (TODO)

### Data Loader Service (Python)

**Location:** `services/data_loader/`

**Purpose:** Loads and parses EDGAR filings from disk.

**Usage:**
```python
from services.data_loader.data_loader import get_filing_data, list_filings
```

### Graph Builder Service (Python)

**Location:** `services/graph_builder/`

**Purpose:** Extracts entities and relationships from filings and builds Neo4j graph.

**Usage:**
```python
from services.graph_builder.graph_builder import GraphBuilder
```

### Downloader Service (TypeScript)

**Location:** `services/downloader/`

**Purpose:** Downloads SEC EDGAR 6-K filings for Foreign Private Issuers with optimized async I/O.

**Technology:**
- TypeScript (strict type checking)
- Node.js (async/await for I/O operations)
- Rate limiting (10 requests/second)
- Sequential downloads

**Build:**
```bash
cd services/downloader
npm install
npm run build
```

**Run:**
```bash
node dist/index.js 2009 2010
```

**Usage from CLI:**
```bash
python -m services.cli.main download --start-year 2009 --end-year 2010
```

### AI Services (Python)

**Location:** `services/ai/`

**Purpose:** AI-powered analysis, extraction, and natural language querying.

**Services:**
- `ai_analyzer.py` - Analyzes graph builder logic and suggests improvements
- `ai_extractor.py` - AI-powered entity extraction from filings
- `cypher_rag.py` - Converts natural language to Cypher queries

**Usage:**
```bash
# Used via CLI
python -m services.cli.main analyze --year 2010 --limit 5
python -m services.cli.main query "Find all companies"
```

### Coordinator Service (Python)

**Location:** `services/coordinator/`

**Purpose:** Manages work queue and job distribution for distributed processing.

**Usage:**
```bash
python -m services.coordinator.main --year 2010 --limit 10 --wait
```

### Worker Service (Python)

**Location:** `services/worker/`

**Purpose:** Processes filings from work queue in distributed system.

**Usage:**
```bash
python -m services.worker.main
```

## Adding New Services

To add a new microservice:

### Python Service:
1. Create a new directory: `services/<service-name>/`
2. Add `__init__.py` to make it a Python package
3. Add service code files
4. Add `main.py` as entry point if needed
5. Update imports in other services if needed

### TypeScript Service:
1. Create a new directory: `services/<service-name>/`
2. Add `package.json` with service dependencies
3. Add `tsconfig.json` for TypeScript
4. Create `src/` directory with service code
5. Add build scripts to `package.json`
6. Update Dockerfile to build the new service

## Architecture Principles

- **Separation of Concerns:** Each service handles a specific domain
- **Type Safety:** TypeScript services use strict type checking
- **Independent Deployment:** Services can be built and deployed separately
- **Shared Configuration:** Common configs (like data directories) via environment variables
- **Language Agnostic:** Services can be written in Python or TypeScript as appropriate

