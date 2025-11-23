# Orion - Document Management & Knowledge Graph System

## 🎯 Project Overview

Orion is an intelligent document management system that leverages Large Language Models (LLMs), Neo4j graph database, and Oracle AI Vector DB to create a comprehensive knowledge graph from organizational documents. The system enables semantic search, relationship discovery, and intelligent document organization.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                            │
│                    (API / CLI / Web Interface)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌───────────────┐        ┌───────────────┐
        │  Python       │        │  LangChain     │
        │  Backend      │◄───────┤  Framework     │
        │  (FastAPI/    │        │  (Orchestration│
        │   Flask)      │        │   & LLM Chain) │
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

### Components

1. **LLM Layer** (Ollama/LM Studio)
   - Local LLM for document processing and semantic understanding
   - Text extraction and summarization
   - Entity recognition and relationship extraction

2. **Neo4j Graph Database**
   - Stores document relationships and metadata
   - Employee, Document, Project, Department nodes
   - WORKED_ON, BELONGS_TO, WROTE, PART_OF relationships

3. **Oracle AI Vector DB**
   - Stores document embeddings for semantic search
   - Vector similarity search for document discovery

4. **Python Backend**
   - API endpoints for document ingestion and querying
   - Integration with LangChain for LLM orchestration
   - Business logic and data processing

5. **LangChain Framework**
   - Orchestrates LLM calls and document processing
   - Manages prompts and chains for document analysis

## 📊 Graph Schema

```
(Employee) -[:WORKED_ON {role, start_date}]-> (Document)
(Author) -[:WROTE {contribution_type}]-> (Document)
(Document) -[:BELONGS_TO {category}]-> (Project)
(Project) -[:PART_OF]-> (Department)
(Employee) -[:MEMBER_OF {role}]-> (Department)
```

See [docs/neo4j_schema.md](docs/neo4j_schema.md) for detailed schema documentation.

## 🚀 Quick Start

### Option 1: Docker (SEC EDGAR Download)

**Prerequisites:**
- Docker and Docker Compose installed
- See [Docker Guide](docs/DOCKER.md) for details

**Note:** Docker orchestration currently supports SEC EDGAR downloads only. Other processes will be added later.

**Quick Start:**
```bash
# Build Docker image
./docker-orchestrator.sh build

# Download filings (default: 2009-2010, 5 workers)
./docker-orchestrator.sh download

# Custom download
./docker-orchestrator.sh download 2020 2021 10

# Or use Make
make build
make download
```

### Option 2: Local Conda Setup

**Prerequisites:**
- **Conda** (Miniconda or Anaconda) - [Download here](https://docs.conda.io/en/latest/miniconda.html)
  - **Note:** This project uses Conda exclusively. All Python packages are managed through conda environments.
- Neo4j Aura Free account (or local Neo4j instance)
- Oracle AI Vector DB account
- Ollama or LM Studio installed locally

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd orion
   ```

3. **Create conda environment**
   ```bash
   # Option 1: Using the setup script (Recommended)
   ./setup_conda.sh
   conda activate orion
   
   # Option 2: Manual setup
   conda env create -f environment.yml
   conda activate orion
   ```
   
   **Note:** This project uses Conda exclusively. All Python packages are managed through the conda environment defined in `environment.yml`.

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Set up Neo4j**
   - **Option A: Neo4j Aura Free**
     - Sign up at https://neo4j.com/cloud/aura-free/
     - Create a new database instance
     - Copy the connection URI and credentials to `.env`
   
   - **Option B: Local Neo4j**
     - Download Neo4j Desktop or use Docker
     - Start Neo4j and update `.env` with local connection details

6. **Set up Ollama (or LM Studio)**
   - **Ollama**: Install from https://ollama.ai/
     - Run: `ollama pull llama2` (or your preferred model)
   
   - **LM Studio**: Install from https://lmstudio.ai/
     - Start the local server and update `LM_STUDIO_BASE_URL` in `.env`

7. **Initialize Neo4j schema**
   ```bash
   python -m src.cli setup-db
   ```

### Verify Installation

```bash
# Test database connections
python -m src.cli test-db --neo4j

# You should see:
# ✓ Successfully connected to Neo4j at <your-uri>
# ✓ Database connection test successful
# ✓ Schema setup completed successfully
```

## 📖 Documentation

All documentation is available in the [`docs/`](docs/) directory:

- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup instructions
- **[CLI Usage](docs/CLI_USAGE.md)** - Command-line interface reference
- **[Download Guide](docs/DOWNLOAD_GUIDE.md)** - SEC EDGAR download instructions
- **[Conda Setup](docs/CONDA_SETUP.md)** - Conda environment configuration
- **[Python Setup](docs/PYTHON_SETUP.md)** - Python installation check
- **[Neo4j Schema](docs/neo4j_schema.md)** - Database schema documentation

## 🚀 CLI Usage

Orion provides a unified CLI interface for all operations:

```bash
# Main CLI entry point
python -m src.cli <command> [options]

# Or use the convenience script
./orion <command> [options]
```

### Available Commands

#### Download SEC EDGAR Filings
```bash
# Download 6-K filings for a date range
python -m src.cli download --start-year 2009 --end-year 2010

# Download to custom directory
python -m src.cli download --start-year 2020 --end-year 2021 --download-dir ./my_filings

# Re-download existing filings
python -m src.cli download --start-year 2009 --end-year 2010 --no-skip-existing
```

#### Database Setup
```bash
# Initialize Neo4j database schema
python -m src.cli setup-db
```

#### Test Connections
```bash
# Test Neo4j connection
python -m src.cli test-db --neo4j

# Test Oracle AI Vector DB connection
python -m src.cli test-db --oracle

# Test both
python -m src.cli test-db
```

#### Run Tests
```bash
# Test SEC EDGAR downloader
python -m src.cli test --download
```

For detailed help on any command:
```bash
python -m src.cli <command> --help
```

## 📁 Project Structure

```
orion/
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── neo4j_connection.py      # Neo4j connection and schema setup
│   │   └── oracle_connection.py     # Oracle AI Vector DB connection (TODO)
│   ├── ingestion/                   # SEC EDGAR filing ingestion
│   │   ├── __init__.py
│   │   ├── sec_companies.py         # Company index parser
│   │   ├── filing_downloader.py     # Filing downloader
│   │   └── main.py                  # Ingestion entry point
│   ├── models/
│   │   └── graph_models.py          # Graph node and relationship models (TODO)
│   ├── services/
│   │   ├── document_service.py      # Document processing service (TODO)
│   │   └── llm_service.py           # LLM integration service (TODO)
│   └── utils/
│       └── __init__.py
├── docs/                            # Documentation
│   ├── CLI_USAGE.md                 # CLI usage guide
│   ├── CONDA_SETUP.md               # Conda setup guide
│   ├── DOWNLOAD_GUIDE.md            # SEC EDGAR download guide
│   ├── INSTALLATION.md              # Installation guide
│   ├── PYTHON_SETUP.md              # Python setup guide
│   └── neo4j_schema.md              # Graph schema documentation
├── tests/                           # Test files (TODO)
├── .env.example                     # Environment variables template
├── .gitignore
├── Dockerfile                       # Docker image definition
├── docker-compose.yml              # Docker orchestration
├── docker-orchestrator.sh          # Docker orchestration script
├── Makefile                        # Make commands for Docker
├── environment.yml                  # Conda environment file (primary)
├── requirements.txt                 # Python dependencies (reference only)
├── setup.py                        # Legacy setup script (use setup_conda.sh)
├── setup_conda.sh                  # Conda setup script (use this)
└── README.md                        # This file
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

- **NEO4J_URI**: Neo4j connection URI (bolt://localhost:7687 or neo4j+s://...)
- **NEO4J_USER**: Neo4j username
- **NEO4J_PASSWORD**: Neo4j password
- **ORACLE_USER**: Oracle AI Vector DB username
- **ORACLE_PASSWORD**: Oracle AI Vector DB password
- **ORACLE_DSN**: Oracle connection string
- **OLLAMA_BASE_URL**: Ollama API endpoint (default: http://localhost:11434)
- **OLLAMA_MODEL**: Model name to use (default: llama2)

**Status**: Week 1-2 Complete ✅ | Next: Core Functionality Implementation

