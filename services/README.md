# Orion Services

This directory contains microservices for the Orion project, following a microservices architecture.

## Structure

```
services/
├── downloader/          # SEC EDGAR Filing Downloader Service
│   ├── src/            # TypeScript source files
│   ├── dist/           # Compiled JavaScript (generated)
│   ├── package.json    # Service dependencies
│   └── tsconfig.json   # TypeScript configuration
└── README.md           # This file
```

## Services

### Downloader Service

**Location:** `services/downloader/`

**Purpose:** Downloads SEC EDGAR 6-K filings for Foreign Private Issuers with optimized async I/O.

**Technology:**
- TypeScript (strict type checking)
- Node.js (async/await for I/O operations)
- Rate limiting (10 requests/second)
- Parallel downloads with configurable workers

**Build:**
```bash
cd services/downloader
npm install
npm run build
```

**Run:**
```bash
node dist/index.js 2009 2010 --max-workers 20
```

**Usage from CLI:**
```bash
python -m src.cli download --start-year 2009 --end-year 2010 --max-workers 20
```

## Adding New Services

To add a new microservice:

1. Create a new directory: `services/<service-name>/`
2. Add `package.json` with service dependencies
3. Add `tsconfig.json` for TypeScript (if using TypeScript)
4. Create `src/` directory with service code
5. Add build scripts to `package.json`
6. Update Dockerfile to build the new service

## Architecture Principles

- **Separation of Concerns:** Each service handles a specific domain
- **Type Safety:** Services use TypeScript for strict type checking
- **Independent Deployment:** Services can be built and deployed separately
- **Shared Configuration:** Common configs (like data directories) via environment variables

