# Orion CLI Usage Guide

## Overview

Orion provides a unified command-line interface for all operations. You can run commands using:

```bash
python -m src.cli <command> [options]
```

Or use the convenience script:
```bash
./orion <command> [options]
```

## Commands

### 1. Download SEC EDGAR Filings

Download 6-K filings from SEC EDGAR for Foreign Private Issuers.

**Usage:**
```bash
python -m src.cli download [options]
```

**Options:**
- `--start-year YEAR` - Starting year (inclusive, default: 2009)
- `--end-year YEAR` - Ending year (inclusive, default: 2010)
- `--no-skip-existing` - Re-download filings even if they already exist
- `--download-dir DIR` - Custom download directory (default: ./Edgar_filings)

**Examples:**
```bash
# Download 2009-2010 filings (default)
python -m src.cli download

# Download specific years
python -m src.cli download --start-year 2020 --end-year 2021

# Download to custom directory
python -m src.cli download --start-year 2009 --end-year 2010 --download-dir ./my_filings

# Re-download existing filings
python -m src.cli download --start-year 2009 --end-year 2010 --no-skip-existing
```

**Output:**
- `Edgar_filings/` - Downloaded filing files
- `fpi_list.csv` - List of companies with 6-K filings
- `fpi_6k_metadata.csv` - Metadata for all downloaded filings
- `metadata/` - Cached SEC company index files

---

### 2. Setup Database

Initialize Neo4j database with schema, indexes, and constraints.

**Usage:**
```bash
python -m src.cli setup-db
```

**What it does:**
- Connects to Neo4j database
- Creates indexes for all node types
- Creates constraints for unique identifiers
- Sets up full-text search indexes

**Prerequisites:**
- Neo4j database must be running
- `.env` file must contain valid Neo4j credentials:
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`

**Example:**
```bash
python -m src.cli setup-db
```

---

### 3. Test Database Connections

Test connections to Neo4j and/or Oracle AI Vector DB.

**Usage:**
```bash
python -m src.cli test-db [options]
```

**Options:**
- `--neo4j` - Test Neo4j connection only
- `--oracle` - Test Oracle AI Vector DB connection only
- (no options) - Test both connections

**Examples:**
```bash
# Test both databases
python -m src.cli test-db

# Test only Neo4j
python -m src.cli test-db --neo4j

# Test only Oracle
python -m src.cli test-db --oracle
```

---

### 4. Run Tests

Run test suite to verify system functionality.

**Usage:**
```bash
python -m src.cli test [options]
```

**Options:**
- `--download` - Test SEC EDGAR downloader

**Examples:**
```bash
# Test downloader
python -m src.cli test --download
```

---

## Getting Help

Get help for any command:

```bash
# General help
python -m src.cli --help

# Command-specific help
python -m src.cli download --help
python -m src.cli setup-db --help
python -m src.cli test-db --help
python -m src.cli test --help
```

## Common Workflows

### Initial Setup
```bash
# 1. Setup Neo4j database
python -m src.cli setup-db

# 2. Test connections
python -m src.cli test-db --neo4j

# 3. Download SEC filings
python -m src.cli download --start-year 2009 --end-year 2010
```

### Downloading Data
```bash
# Download a specific year range
python -m src.cli download --start-year 2020 --end-year 2021

# Download to a specific directory
python -m src.cli download --start-year 2009 --end-year 2010 --download-dir ./data/edgar
```

### Resuming Downloads
The downloader automatically skips already downloaded filings. To re-download:
```bash
python -m src.cli download --start-year 2009 --end-year 2010 --no-skip-existing
```

## Error Handling

- All commands provide clear error messages
- Database connection errors include troubleshooting hints
- Download errors are logged with details
- Use `--help` for command-specific information

## Environment Variables

Make sure your `.env` file is configured:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Oracle AI Vector DB Configuration (optional)
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=your_host:1521/your_service
```

