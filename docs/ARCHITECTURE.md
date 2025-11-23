# Orion Architecture

## Overview

Orion is an intelligent document management system that leverages Large Language Models (LLMs), Neo4j graph database, and Oracle AI Vector DB to create a comprehensive knowledge graph from organizational documents.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                            │
│                    (CLI / API / Web Interface)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌───────────────┐        ┌───────────────┐
        │  Python       │        │  LangChain     │
        │  Backend      │◄───────┤  Framework     │
        │  (CLI/API)    │        │  (Orchestration│
        │               │        │   & LLM Chain) │
        └───────┬───────┘        └───────┬───────┘
                │                        │
    ┌───────────┼───────────┐            │
    │           │           │            │
    ▼           ▼           ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│  Neo4j  │ │ Oracle  │ │ Ollama  │ │ Document │
│  Graph  │ │ AI      │ │ / LM    │ │ Parser   │
│  DB     │ │ Vector  │ │ Studio  │ │          │
│         │ │ DB      │ │         │ │          │
└─────────┘ └─────────┘ └─────────┘ └──────────┘
```

## Components

### 1. CLI Interface
- **Location**: `src/cli.py`
- **Purpose**: Unified command-line interface for all operations
- **Commands**:
  - `download` - Download SEC EDGAR filings
  - `setup-db` - Initialize database schema
  - `test-db` - Test database connections
  - `test` - Run test suite

### 2. Database Layer

#### Neo4j Graph Database
- **Location**: `src/database/neo4j_connection.py`
- **Purpose**: Store document relationships and metadata
- **Schema**: See [neo4j_schema.md](neo4j_schema.md)
- **Node Types**: Employee, Document, Project, Department, Author
- **Relationships**: WORKED_ON, BELONGS_TO, WROTE, PART_OF, MEMBER_OF

#### Oracle AI Vector DB
- **Location**: `src/database/oracle_connection.py`
- **Purpose**: Store document embeddings for semantic search
- **Status**: Basic connection implemented, vector operations TODO

### 3. Ingestion Layer

#### SEC EDGAR Ingestion
- **Location**: `src/ingestion/`
- **Components**:
  - `sec_companies.py` - Company index parser
  - `filing_downloader.py` - Filing downloader and exhibit extractor
  - `main.py` - Entry point
- **Features**:
  - Downloads 6-K filings for Foreign Private Issuers
  - Extracts EX-99 exhibits
  - Respects SEC rate limits
  - Resume capability

### 4. LLM Integration (TODO)
- **Location**: `src/services/llm_service.py` (to be created)
- **Purpose**: Document processing and semantic understanding
- **Integration**: LangChain with Ollama/LM Studio
- **Features** (planned):
  - Text extraction and summarization
  - Entity recognition
  - Relationship extraction

### 5. Document Processing (TODO)
- **Location**: `src/services/document_service.py` (to be created)
- **Purpose**: Process and analyze documents
- **Features** (planned):
  - Document parsing
  - Embedding generation
  - Graph node creation

## Data Flow

### Document Ingestion Flow
```
1. SEC EDGAR Download
   └─> filing_downloader.py
       └─> Downloads 6-K filings
       └─> Extracts EX-99 exhibits
       └─> Saves to Edgar_filings/

2. Document Processing (TODO)
   └─> document_service.py
       └─> Parse documents
       └─> Extract entities
       └─> Generate embeddings

3. LLM Analysis (TODO)
   └─> llm_service.py
       └─> Summarize documents
       └─> Extract relationships
       └─> Identify entities

4. Graph Creation (TODO)
   └─> Create nodes in Neo4j
   └─> Create relationships
   └─> Store metadata

5. Vector Storage (TODO)
   └─> Store embeddings in Oracle
   └─> Enable semantic search
```

## Technology Stack

### Core Technologies
- **Python**: 3.9+ (managed via Conda)
- **Conda**: Environment and dependency management
- **Neo4j**: Graph database
- **Oracle AI Vector DB**: Vector storage
- **LangChain**: LLM orchestration framework

### Python Packages
- **neo4j**: Neo4j driver
- **oracledb**: Oracle database driver
- **langchain**: LLM framework
- **langchain-ollama**: Ollama integration
- **requests**: HTTP client
- **beautifulsoup4**: HTML parsing
- **tqdm**: Progress bars

## Project Structure

```
orion/
├── src/
│   ├── cli.py                    # Main CLI interface
│   ├── database/                 # Database connections
│   │   ├── neo4j_connection.py
│   │   └── oracle_connection.py
│   ├── ingestion/               # SEC EDGAR ingestion
│   │   ├── sec_companies.py
│   │   ├── filing_downloader.py
│   │   └── main.py
│   ├── services/                # Business logic (TODO)
│   │   ├── document_service.py
│   │   └── llm_service.py
│   └── models/                  # Data models (TODO)
│       └── graph_models.py
├── docs/                        # Documentation
├── environment.yml              # Conda environment
└── setup_conda.sh              # Setup script
```

## Development Status

### ✅ Completed
- Project structure
- Conda environment setup
- Neo4j connection and schema
- SEC EDGAR ingestion pipeline
- CLI interface
- Documentation

### 🚧 In Progress
- Oracle AI Vector DB integration
- Document processing service
- LLM integration

### 📋 Planned
- Graph node creation from documents
- Relationship discovery
- Semantic search
- API endpoints
- Web interface

## Configuration

### Environment Variables
All configuration is managed through `.env` file:
- Database connections (Neo4j, Oracle)
- LLM endpoints (Ollama, LM Studio)
- Application settings

See main [README.md](../README.md) for configuration details.

## Dependencies

All dependencies are managed through Conda:
- Defined in `environment.yml`
- Installed via `conda env create -f environment.yml`
- No pip/venv installation supported

See [CONDA_SETUP.md](CONDA_SETUP.md) for details.

