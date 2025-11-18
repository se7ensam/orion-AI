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

See [schema/neo4j_schema.md](schema/neo4j_schema.md) for detailed schema documentation.

## 🚀 Quick Start

### Prerequisites

- **Conda** (Miniconda or Anaconda) - [Download here](https://docs.conda.io/en/latest/miniconda.html)
  - Or Python 3.9+ with pip/venv
- Neo4j Aura Free account (or local Neo4j instance)
- Oracle AI Vector DB account
- Ollama or LM Studio installed locally

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd orion
   ```

2. **Create conda environment** (Recommended)
   ```bash
   # Option A: Using conda (Recommended)
   conda env create -f environment.yml
   conda activate orion
   
   # Or use the setup script
   ./setup_conda.sh
   ```
   
   **Alternative: Using pip/venv**
   ```bash
   # Option B: Using pip/venv
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Set up Neo4j**
   - **Option A: Neo4j Aura Free**
     - Sign up at https://neo4j.com/cloud/aura-free/
     - Create a new database instance
     - Copy the connection URI and credentials to `.env`
   
   - **Option B: Local Neo4j**
     - Download Neo4j Desktop or use Docker
     - Start Neo4j and update `.env` with local connection details

5. **Set up Ollama (or LM Studio)**
   - **Ollama**: Install from https://ollama.ai/
     - Run: `ollama pull llama2` (or your preferred model)
   
   - **LM Studio**: Install from https://lmstudio.ai/
     - Start the local server and update `LM_STUDIO_BASE_URL` in `.env`

6. **Initialize Neo4j schema**
   ```bash
   python src/database/neo4j_connection.py
   ```

### Verify Installation

```bash
# Test Neo4j connection
python src/database/neo4j_connection.py

# You should see:
# ✓ Successfully connected to Neo4j at <your-uri>
# ✓ Database connection test successful
# ✓ Schema setup completed successfully
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
├── schema/
│   └── neo4j_schema.md              # Graph schema documentation
├── tests/                           # Test files (TODO)
├── .env.example                     # Environment variables template
├── .gitignore
├── environment.yml                  # Conda environment file
├── requirements.txt                 # Python dependencies (pip)
├── setup.py                        # Setup script
├── setup_conda.sh                  # Conda setup script
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

## 📋 Development Roadmap

### Week 1-2: Planning & Setup ✅
- [x] Project structure and architecture design
- [x] Neo4j connection and schema setup
- [x] Basic repository setup
- [x] Documentation (README, schema docs)

### Week 3-4: Core Functionality (TODO)
- [ ] Document ingestion pipeline
- [ ] LLM integration for document analysis
- [ ] Oracle AI Vector DB integration
- [ ] Graph node and relationship creation

### Week 5-6: Advanced Features (TODO)
- [ ] Semantic search capabilities
- [ ] Relationship discovery algorithms
- [ ] API endpoints (FastAPI/Flask)
- [ ] Query interface

### Week 7-8: Testing & Deployment (TODO)
- [ ] Unit and integration tests
- [ ] Performance optimization
- [ ] Deployment documentation
- [ ] Production setup

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## 📝 License

[Add your license here]

## 📧 Contact

[Add contact information]

---

**Status**: Week 1-2 Complete ✅ | Next: Core Functionality Implementation

