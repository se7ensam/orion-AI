# Pending Development - Orion Data Storage Architecture

## Executive Summary

This document outlines what needs to be implemented to align the Orion project with the specified data storage architecture. The current system has **downloading and basic database connections** in place, but **lacks the complete data processing pipeline** for graph database and vector database integration.

---

## 1. RAW FILE STORAGE ✅ PARTIALLY COMPLETE

### Current State:
- ✅ **Files are stored on disk** (not in database)
- ✅ **Downloader service exists** (`services/downloader/`)
- ✅ **Files stored in**: `data/edgar_filings/{Company Name}/{Year}_{Company Name}_{CIK}/{Accession Number}/`
- ✅ **File structure includes**: `filing.html`, `{accession}.txt`, `EX-99.*.txt` exhibits

### Required Structure:
```
/data/filings/{year}/{original_filename}.htm
```

### ⚠️ PENDING:
1. **Reorganize file structure** to match requirement:
   - Current: `data/edgar_filings/{Company}/{Year}_{Company}_{CIK}/{Accession}/filing.html`
   - Required: `data/filings/{year}/{original_filename}.htm`
   - **Action**: Create migration/restructuring script

2. **Create `data/processed/` directory** for processed/intermediate files

3. **File naming standardization**:
   - Extract original filename from EDGAR metadata
   - Store as `{original_filename}.htm` instead of generic `filing.html`

---

## 2. GRAPH DATABASE (Neo4j) ⚠️ SCHEMA MISMATCH

### Current State:
- ✅ **Neo4j connection exists** (`src/database/neo4j_connection.py`)
- ✅ **Basic schema setup** implemented
- ❌ **Wrong schema** - Currently has: `Employee`, `Document`, `Project`, `Department`, `Author`
- ❌ **No EDGAR-specific nodes** - Missing: `Company`, `Person`, `Rating`, `Event`, `Debenture`, `Sector`
- ❌ **No EDGAR-specific relationships** - Missing: `OWNS`, `RATED_BY`, `SUBSIDIARY_OF`, `HAS_EVENT`, `WORKS_AT`
- ❌ **No data loading logic** - No code to extract entities from EDGAR filings and create graph nodes

### Required Schema:
```cypher
(:Company)
(:Person)
(:Rating)
(:Event)
(:Debenture)
(:Sector)

(:Company)-[:OWNS]->(:Company)
(:Company)-[:RATED_BY]->(:Rating)
(:Company)-[:SUBSIDIARY_OF]->(:Company)
(:Company)-[:HAS_EVENT]->(:Event)
(:Person)-[:WORKS_AT]->(:Company)
```

### ⚠️ PENDING:
1. **Update Neo4j schema** (`src/database/neo4j_connection.py`):
   - Remove old schema (Employee, Document, Project, Department, Author)
   - Add new nodes: `Company`, `Person`, `Rating`, `Event`, `Debenture`, `Sector`
   - Add new relationships: `OWNS`, `RATED_BY`, `SUBSIDIARY_OF`, `HAS_EVENT`, `WORKS_AT`
   - Update constraints and indexes

2. **Create `src/graph_builder.py`**:
   - Parse EDGAR filings (HTML/TXT files)
   - Extract structured entities:
     - Company information (name, CIK, industry, etc.)
     - People (executives, directors, signatories)
     - Ratings (credit ratings, analyst ratings)
     - Events (mergers, acquisitions, filings, announcements)
     - Debentures (bonds, debt instruments)
     - Sectors (industry classifications)
   - Extract relationships between entities
   - Create Cypher queries to insert nodes and relationships
   - Use LLM (via LangChain) for entity extraction if needed

3. **Create `neo4j/seed.cypher`**:
   - Sample Cypher queries for testing
   - Example data insertion patterns

4. **Create `neo4j/docker-compose.yml`**:
   - Docker Compose configuration for Neo4j
   - Volume mounts for data persistence
   - Environment variables for authentication

5. **Update `src/cli.py`**:
   - Add command: `python -m src.cli load-graph` to process filings and build graph

---

## 3. VECTOR DATABASE (Chroma or Oracle Vector Search) ⚠️ INCOMPLETE

### Current State:
- ✅ **Oracle connection exists** (`src/database/oracle_connection.py`)
- ✅ **Basic connection test** implemented
- ❌ **No vector operations** - Only connection test, no embedding storage
- ❌ **No chunking logic** - No code to split documents into chunks
- ❌ **No embedding generation** - No integration with embedding models
- ❌ **No vector search** - No similarity search implementation

### Required Schema:
Each chunk record must contain:
- `filing_id` (unique identifier)
- `company` (company name)
- `text_chunk` (chunked text)
- `embedding` (vector)
- `timestamp` (when processed)
- `source_file_path` (path to original file)

### ⚠️ PENDING:
1. **Create `src/vector_store.py`**:
   - **Chunking logic**:
     - Split EDGAR filings into semantic chunks (e.g., 500-1000 tokens)
     - Preserve context (overlap between chunks)
     - Handle HTML/TXT format
   - **Embedding generation**:
     - Integrate with embedding model (e.g., via LangChain, Ollama, or OpenAI)
     - Generate embeddings for each chunk
   - **Vector storage**:
     - Store chunks in Oracle Vector DB (or Chroma if switching)
     - Store metadata (filing_id, company, timestamp, source_file_path)
   - **Vector search**:
     - Implement similarity search function
     - Return top-k similar chunks with metadata

2. **Update `src/database/oracle_connection.py`**:
   - Add methods for:
     - Creating vector table/collection
     - Inserting embeddings
     - Querying similar vectors
     - Managing chunk metadata

3. **Decide on vector database**:
   - **Option A**: Oracle Vector Search (already has connection)
   - **Option B**: Chroma (easier setup, Python-native)
   - **Action**: Choose one and implement accordingly

4. **Update `src/cli.py`**:
   - Add command: `python -m src.cli vectorize` to process filings and generate embeddings

---

## 4. HYBRID RAG PIPELINE ❌ NOT IMPLEMENTED

### Current State:
- ❌ **No RAG pipeline** - No code for combining graph and vector search
- ❌ **No LLM integration** - LangChain packages installed but not used
- ❌ **No query interface** - No way to ask questions

### Required Flow:
```
1. Natural language query → LLM
2. LLM converts to Cypher query → Neo4j (get graph facts)
3. LLM extracts semantic intent → Vector search (get semantic context)
4. Combine graph facts + semantic context → LLM
5. LLM generates final answer
```

### ⚠️ PENDING:
1. **Create `src/rag_agent.py`**:
   - **Query processing**:
     - Accept natural language queries
     - Use LLM to generate Cypher queries from natural language
     - Use LLM to extract semantic search terms
   - **Dual retrieval**:
     - Execute Cypher query → get structured facts from Neo4j
     - Execute vector search → get semantic context from vector DB
   - **Answer generation**:
     - Combine graph facts + semantic chunks
     - Pass to LLM for final answer generation
     - Return formatted response

2. **LLM Integration**:
   - Configure LangChain with Ollama/LM Studio
   - Create prompt templates for:
     - Cypher query generation
     - Semantic search query extraction
     - Answer synthesis
   - Handle streaming responses (optional)

3. **Create `src/main.py`**:
   - Main entry point for RAG queries
   - CLI or API interface for asking questions
   - Example: `python -m src.main query "What companies does Company X own?"`

---

## 5. FILE + FOLDER REQUIREMENTS ⚠️ PARTIALLY COMPLETE

### Current Structure:
```
orion/
├── data/
│   ├── edgar_filings/          ✅ Exists (wrong structure)
│   ├── fpi_6k_metadata.csv     ✅ Exists
│   ├── fpi_list.csv            ✅ Exists
│   └── metadata/               ✅ Exists
├── src/
│   ├── cli.py                  ✅ Exists
│   ├── database/               ✅ Exists
│   │   ├── neo4j_connection.py ✅ Exists
│   │   └── oracle_connection.py ✅ Exists
│   └── ingestion/              ✅ Exists
├── services/
│   └── downloader/             ✅ Exists (TypeScript)
└── requirements.txt            ✅ Exists
```

### Required Structure:
```
orion/
├── data/
│   ├── filings/                ❌ Missing (needs reorganization)
│   └── processed/              ❌ Missing
├── neo4j/
│   ├── docker-compose.yml      ❌ Missing
│   └── seed.cypher             ❌ Missing
└── src/
    ├── data_loader.py          ❌ Missing
    ├── graph_builder.py        ❌ Missing
    ├── vector_store.py         ❌ Missing
    ├── rag_agent.py            ❌ Missing
    ├── stock_api.py            ❌ Missing (optional?)
    ├── ui_app.py               ❌ Missing (optional?)
    └── main.py                 ❌ Missing
```

### ⚠️ PENDING:
1. **Create `src/data_loader.py`**:
   - Load EDGAR filings from disk
   - Parse HTML/TXT files
   - Extract metadata (company, date, accession number, etc.)
   - Provide unified interface for accessing filings

2. **Create `src/graph_builder.py`**:
   - See section 2 above

3. **Create `src/vector_store.py`**:
   - See section 3 above

4. **Create `src/rag_agent.py`**:
   - See section 4 above

5. **Create `src/main.py`**:
   - Main entry point for RAG queries
   - CLI interface for interactive queries

6. **Create `neo4j/docker-compose.yml`**:
   - Neo4j service configuration
   - Port mapping (7474 for browser, 7687 for bolt)
   - Volume for data persistence

7. **Create `neo4j/seed.cypher`**:
   - Sample data and queries for testing

8. **Reorganize `data/` directory**:
   - Create `data/filings/` with `{year}/{filename}.htm` structure
   - Create `data/processed/` for intermediate files
   - Optionally keep `data/edgar_filings/` for backward compatibility or migrate

9. **Optional files** (if needed):
   - `src/stock_api.py` - If integrating stock market data
   - `src/ui_app.py` - If building a web UI (Flask/FastAPI)

---

## 6. SEPARATION OF CONCERNS ✅ COMPLIANT (SO FAR)

### Current State:
- ✅ **Raw files stored on disk only** (not in Neo4j or vector DB)
- ✅ **No long text in Neo4j** (schema exists but no data loaded yet)
- ✅ **No embeddings stored yet** (vector DB not implemented)

### ⚠️ PENDING:
- **Ensure compliance** when implementing:
  - `graph_builder.py` should NOT store full document text in Neo4j
  - `vector_store.py` should NOT store relationships in vector DB
  - Only metadata and structured entities in Neo4j
  - Only chunks and embeddings in vector DB

---

## 7. DEPENDENCIES & INFRASTRUCTURE ⚠️ PARTIALLY READY

### Current State:
- ✅ **Python packages installed** (via `environment.yml`):
  - `neo4j`, `oracledb`, `langchain`, `langchain-ollama`, `langchain-neo4j`
  - `requests`, `beautifulsoup4`, `tqdm`
- ✅ **TypeScript downloader** built and working
- ❌ **No embedding model configured** - Need to choose and configure
- ❌ **No LLM configured** - Ollama/LM Studio not set up

### ⚠️ PENDING:
1. **Add embedding dependencies** (if needed):
   - `sentence-transformers` (for local embeddings)
   - OR configure OpenAI API key (if using OpenAI embeddings)
   - OR configure Ollama embeddings endpoint

2. **Configure LLM**:
   - Set up Ollama or LM Studio
   - Configure LangChain to use local LLM
   - Test LLM connection

3. **Update `environment.yml`**:
   - Add any missing packages for embeddings/LLM

---

## SUMMARY: Priority Order

### Phase 1: Foundation (Critical)
1. ✅ **File reorganization** - Restructure `data/filings/` to required format
2. ✅ **Update Neo4j schema** - Replace old schema with EDGAR-specific nodes/relationships
3. ✅ **Create `src/data_loader.py`** - Unified interface for loading filings

### Phase 2: Graph Database (High Priority)
4. ✅ **Create `src/graph_builder.py`** - Extract entities and build graph
5. ✅ **Create `neo4j/docker-compose.yml`** - Neo4j infrastructure
6. ✅ **Test graph creation** - Load sample filings and verify graph structure

### Phase 3: Vector Database (High Priority)
7. ✅ **Create `src/vector_store.py`** - Chunking, embedding, vector storage
8. ✅ **Choose vector DB** - Oracle Vector Search or Chroma
9. ✅ **Test vector search** - Verify similarity search works

### Phase 4: RAG Pipeline (Medium Priority)
10. ✅ **Create `src/rag_agent.py`** - Hybrid retrieval and answer generation
11. ✅ **Configure LLM** - Set up Ollama/LangChain
12. ✅ **Create `src/main.py`** - Query interface

### Phase 5: Polish (Low Priority)
13. ✅ **Create `neo4j/seed.cypher`** - Sample data
14. ✅ **Optional: `src/stock_api.py`** - Stock data integration
15. ✅ **Optional: `src/ui_app.py`** - Web UI

---

## ESTIMATED EFFORT

- **Phase 1**: 2-3 days
- **Phase 2**: 3-5 days
- **Phase 3**: 3-5 days
- **Phase 4**: 4-6 days
- **Phase 5**: 2-3 days

**Total**: ~14-22 days of development

---

## NOTES

- The current downloader is working well and doesn't need changes (except file structure reorganization)
- The existing Neo4j and Oracle connections are good starting points
- LangChain is already in dependencies, so LLM integration should be straightforward
- Consider using **Chroma** instead of Oracle Vector Search for easier setup (Python-native, no database setup needed)
- Entity extraction from EDGAR filings will likely require LLM assistance (structured data extraction is complex)

