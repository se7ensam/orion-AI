# Orion Frontend - Quick Start Guide

## Overview

The Orion frontend is a Streamlit web application that provides a user-friendly interface for querying the Neo4j graph database using natural language queries.

## Quick Start

### 1. Start Required Services

```bash
# Start Neo4j and Ollama
docker-compose up -d neo4j ollama

# Or use Make
make neo4j
make ollama
```

### 2. Start Frontend

**Option A: Docker (Recommended)**
```bash
docker-compose up -d frontend

# Or use Make
make frontend
```

**Option B: Local**
```bash
conda activate orion
streamlit run frontend/app.py
```

### 3. Access Frontend

Open your browser: **http://localhost:8501**

## Features

### Main Interface

- **Query Input**: Large text area for natural language questions
- **Query Button**: Execute your query
- **Results Table**: Interactive display of query results
- **Cypher Display**: View the generated Cypher query
- **Download**: Export results as CSV

### Sidebar

- **Settings**: 
  - LLM Model selection (llama3.2, llama3, llama2, etc.)
  - Max results limit
  - Show/hide Cypher queries
- **Example Queries**: Click to use pre-written queries
- **Connection Status**: Monitor RAG and Neo4j connections
- **Help**: Usage tips and information

## Example Queries

Try these example queries:

1. **Find Companies**
   - "Find all companies"
   - "Show me companies in the banking sector"
   - "Find companies with CIK 0001234567"

2. **Find People**
   - "Who works at Apple Inc?"
   - "Find all CEOs"
   - "Show me directors at companies"

3. **Find Events**
   - "What events happened at Apple Inc?"
   - "Find all acquisition events"
   - "Show me financial results from 2010"

4. **Find Relationships**
   - "What companies does Apple own?"
   - "Find subsidiaries of Banco Santander"
   - "Show me the ownership chain for Apple"

## Troubleshooting

### Frontend Won't Start

```bash
# Check if port is available
lsof -i :8501

# Check Docker logs
docker-compose logs frontend
# Or
make frontend-logs
```

### Connection Errors

**Cypher RAG Error:**
```bash
# Ensure Ollama is running
docker-compose up -d ollama
ollama pull llama3.2
```

**Neo4j Error:**
```bash
# Ensure Neo4j is running
docker-compose up -d neo4j
# Check connection
python -m src.cli test-db --neo4j
```

### No Results

```bash
# Check if graph has data
python -m src.cli load-graph --year 2010 --limit 10

# Verify in Neo4j Browser
# http://localhost:7474
# Run: MATCH (c:Company) RETURN c LIMIT 10
```

## Configuration

### Environment Variables

The frontend uses the same `.env` file as the CLI:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=orion123
OLLAMA_BASE_URL=http://localhost:11434
```

### Streamlit Config

Edit `frontend/.streamlit/config.toml` to customize:
- Port number
- Theme colors
- Server settings

## Development

### Local Development

```bash
# Activate environment
conda activate orion

# Run with auto-reload
streamlit run frontend/app.py --server.runOnSave=true
```

### Customization

Edit `frontend/app.py` to:
- Change UI styling
- Add new example queries
- Modify result formatting
- Add new features

## Architecture

```
User Browser (Port 8501)
    ↓
Streamlit Frontend
    ↓
Cypher RAG Service (Ollama LLM)
    ↓
Neo4j Database (Port 7687)
```

## See Also

- [Frontend README](../frontend/README.md) - Detailed frontend documentation
- [Cypher RAG Guide](CYPHER_RAG.md) - RAG service details
- [CLI Usage](CLI_USAGE.md) - Command-line interface
- [Neo4j Usage](NEO4J_USAGE.md) - Manual Cypher queries

