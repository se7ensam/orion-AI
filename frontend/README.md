# Orion Frontend - Streamlit Web Interface

A user-friendly web interface for querying the Neo4j graph database using natural language queries powered by Cypher RAG.

## Features

- 🎨 **Modern UI**: Clean, intuitive Streamlit interface
- 💬 **Natural Language Queries**: Ask questions in plain English
- 🔍 **Cypher Query Display**: See the generated Cypher queries
- 📊 **Interactive Results**: View results in tables with download options
- ⚙️ **Configurable**: Choose LLM models and result limits
- 📝 **Example Queries**: Quick access to common queries
- 🔌 **Connection Status**: Monitor service connections

## Prerequisites

1. **Services Running**:
   ```bash
   docker-compose up -d neo4j ollama
   ```

2. **Dependencies Installed**:
   ```bash
   conda env create -f environment.yml
   conda activate orion
   ```

## Running the Frontend

### Option 1: Docker (Recommended)

```bash
# Start all services including frontend
docker-compose up -d

# Or start just frontend (if other services are running)
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend
```

Access the frontend at: **http://localhost:8501**

### Option 2: Local Development

```bash
# Activate conda environment
conda activate orion

# Run Streamlit
streamlit run frontend/app.py

# Or with custom port
streamlit run frontend/app.py --server.port 8502
```

Access the frontend at: **http://localhost:8501** (or your custom port)

## Usage

1. **Enter Query**: Type your question in natural language
   - "Find all companies"
   - "Who works at Apple Inc?"
   - "Find all CEOs"

2. **Configure Settings** (Sidebar):
   - Select LLM model (llama3.2, llama3, llama2, etc.)
   - Set max results limit
   - Toggle Cypher query display

3. **Execute Query**: Click "Query" button

4. **View Results**:
   - See generated Cypher query (if enabled)
   - View results in interactive table
   - Download results as CSV

5. **Use Examples**: Click example queries in sidebar for quick access

## Example Queries

- **Companies**: "Find all companies", "Show me companies in the banking sector"
- **People**: "Who works at Apple Inc?", "Find all CEOs", "Show me directors"
- **Events**: "What events happened at Apple Inc?", "Find all acquisition events"
- **Relationships**: "What companies does Apple own?", "Find subsidiaries of Banco Santander"

## Features

### Sidebar

- **Settings**: Model selection, max results
- **Example Queries**: Quick access to common queries
- **Connection Status**: Monitor RAG and Neo4j connections
- **Help**: Usage tips and information

### Main Area

- **Query Input**: Large text area for natural language queries
- **Query Button**: Execute query
- **Results Display**: Interactive table with download option
- **Cypher Display**: View generated Cypher queries

## Configuration

### Environment Variables

The frontend uses the same environment variables as the CLI:

- `NEO4J_URI`: Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `orion123`)
- `OLLAMA_BASE_URL`: Ollama API URL (default: `http://localhost:11434`)

### Streamlit Configuration

Create `.streamlit/config.toml` for custom configuration:

```toml
[server]
port = 8501
address = "0.0.0.0"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Troubleshooting

### Frontend Won't Start

- Check if port 8501 is available: `lsof -i :8501`
- Verify dependencies: `conda list streamlit`
- Check Docker logs: `docker-compose logs frontend`

### Connection Errors

- **Cypher RAG Error**: Ensure Ollama is running
  ```bash
  docker-compose up -d ollama
  ollama pull llama3.2
  ```

- **Neo4j Error**: Ensure Neo4j is running
  ```bash
  docker-compose up -d neo4j
  ```

### Query Errors

- Check if graph has data: `python -m src.cli load-graph --year 2010 --limit 10`
- Verify model is available: `ollama list`
- Try a simpler query first

## Development

### Local Development Setup

```bash
# Install dependencies
conda env create -f environment.yml
conda activate orion

# Run in development mode (auto-reload)
streamlit run frontend/app.py --server.runOnSave=true
```

### File Structure

```
frontend/
├── app.py          # Main Streamlit application
└── README.md       # This file
```

### Customization

Edit `frontend/app.py` to customize:
- UI styling (CSS in `st.markdown`)
- Example queries
- Default settings
- Result formatting

## Architecture

```
┌─────────────────────────────────────┐
│     Streamlit Frontend (Port 8501) │
│                                     │
│  ┌───────────────────────────────┐ │
│  │   User Input (Natural Lang)   │ │
│  └──────────────┬────────────────┘ │
│                 │                   │
│  ┌──────────────▼────────────────┐ │
│  │   Cypher RAG Service           │ │
│  │   (Ollama LLM)                 │ │
│  └──────────────┬────────────────┘ │
│                 │                   │
│  ┌──────────────▼────────────────┐ │
│  │   Neo4j Database               │ │
│  │   (Port 7687)                  │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## See Also

- [Cypher RAG Documentation](../docs/CYPHER_RAG.md) - RAG service details
- [CLI Usage Guide](../docs/CLI_USAGE.md) - Command-line interface
- [Neo4j Usage Guide](../docs/NEO4J_USAGE.md) - Manual Cypher queries

