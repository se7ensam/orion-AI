# Cypher RAG - Natural Language to Cypher Query Conversion

## Overview

The Cypher RAG (Retrieval-Augmented Generation) service converts natural language questions into Cypher queries for Neo4j graph database. This allows users to query the graph using plain English instead of writing Cypher queries manually.

## Features

- **Natural Language Processing**: Convert questions like "Find all companies" or "Who works at Apple Inc?" into Cypher queries
- **Schema-Aware**: The LLM understands the complete graph schema (nodes, relationships, properties)
- **Automatic Retry**: If a query fails, the system automatically retries with error correction
- **Query Validation**: Basic validation to prevent dangerous operations
- **Formatted Results**: Clean, tabular display of query results
- **Interactive Mode**: Run queries interactively or as single commands

## Prerequisites

1. **Ollama Running**: The service uses Ollama for LLM inference
   ```bash
   docker-compose up -d ollama
   # Or install Ollama locally: https://ollama.ai/
   ```

2. **Neo4j Running**: Neo4j database must be running and accessible
   ```bash
   docker-compose up -d neo4j
   ```

3. **Model Available**: The `llama3.2` model (or your preferred model) must be available
   ```bash
   ollama pull llama3.2
   ```

## Usage

### Basic Query

```bash
python -m src.cli query "Find all companies"
```

### Show Generated Cypher Query

```bash
python -m src.cli query "Who works at Apple Inc?" --show-cypher
```

### Interactive Mode

```bash
python -m src.cli query
```

This enters interactive mode where you can ask multiple questions:
```
💬 Enter your question: Find all companies
💬 Enter your question: Who are the CEOs?
💬 Enter your question: exit
```

### Options

- `--show-cypher`: Display the generated Cypher query
- `--max-rows N`: Limit displayed results (default: 50)
- `--model MODEL`: Use a different Ollama model (default: llama3.2)

## Example Queries

### Find Companies

```bash
python -m src.cli query "Find all companies"
python -m src.cli query "Show me companies in the banking sector"
python -m src.cli query "Find companies with CIK 0001234567"
```

### Find People

```bash
python -m src.cli query "Who works at Apple Inc?"
python -m src.cli query "Find all CEOs"
python -m src.cli query "Show me directors at companies"
```

### Find Events

```bash
python -m src.cli query "What events happened at Apple Inc?"
python -m src.cli query "Find all acquisition events"
python -m src.cli query "Show me financial results from 2010"
```

### Find Relationships

```bash
python -m src.cli query "What companies does Apple own?"
python -m src.cli query "Find subsidiaries of Banco Santander"
python -m src.cli query "Show me the ownership chain for Apple"
```

### Complex Queries

```bash
python -m src.cli query "Find all companies that had acquisitions in 2010"
python -m src.cli query "Show me CEOs who work at banking companies"
python -m src.cli query "Find companies with more than 5 employees"
```

## How It Works

1. **Schema Context**: The RAG service includes complete graph schema information:
   - Node types (Company, Person, Event, Sector)
   - Relationship types (OWNS, WORKS_AT, HAS_EVENT, etc.)
   - Property names and types
   - Example query patterns

2. **LLM Generation**: The natural language question is sent to Ollama LLM with:
   - Schema context
   - Example patterns
   - Rules for Cypher syntax

3. **Query Validation**: Generated queries are validated for:
   - Basic syntax correctness
   - Safety (no write operations without MATCH)
   - Required clauses (MATCH, RETURN)

4. **Execution**: Validated queries are executed against Neo4j

5. **Error Handling**: If a query fails:
   - Error message is captured
   - LLM is asked to fix the query
   - Retry with corrected query (up to 2 retries)

6. **Result Formatting**: Results are displayed in a clean table format

## Graph Schema Reference

The RAG service understands the following schema:

### Node Types

- **Company**: `id`, `cik`, `name`, `sic_code`, `sic_description`, `fiscal_year_end`, `address_*`, `phone`, `sec_file_number`
- **Person**: `id`, `name`, `title`, `role_type` (CEO, Director, Officer, Signatory, Contact, Executive)
- **Event**: `id`, `event_type`, `title`, `event_date`, `filing_id`, `description`
- **Sector**: `id`, `sic_code`, `name`, `description`

### Relationship Types

- **OWNS**: `(:Company)-[:OWNS]->(:Company)` - Company ownership
- **SUBSIDIARY_OF**: `(:Company)-[:SUBSIDIARY_OF]->(:Company)` - Subsidiary relationship
- **WORKS_AT**: `(:Person)-[:WORKS_AT]->(:Company)` - Employment relationship
- **HAS_EVENT**: `(:Company)-[:HAS_EVENT]->(:Event)` - Company events
- **BELONGS_TO_SECTOR**: `(:Company)-[:BELONGS_TO_SECTOR]->(:Sector)` - Sector classification

## Troubleshooting

### "Cypher RAG is not available"

- Ensure Ollama is running: `docker-compose up -d ollama`
- Check Ollama is accessible: `curl http://localhost:11434/api/tags`
- Verify model is downloaded: `ollama list`

### "Failed to connect to Neo4j"

- Ensure Neo4j is running: `docker-compose up -d neo4j`
- Check connection settings in `.env`:
  - `NEO4J_URI=bolt://localhost:7687`
  - `NEO4J_USER=neo4j`
  - `NEO4J_PASSWORD=orion123`

### Query Generation Errors

- Try rephrasing your question
- Use `--show-cypher` to see the generated query
- Check if the query makes sense for the schema
- Ensure the graph has data: `python -m src.cli load-graph --year 2010 --limit 10`

### Model Not Found

- Download the model: `ollama pull llama3.2`
- Or specify a different model: `--model llama2`

## Limitations

1. **Read-Only**: The RAG service only generates read queries (MATCH, RETURN). Write operations are blocked.

2. **Schema Dependency**: The service works best when questions align with the actual graph schema. Complex questions may need refinement.

3. **LLM Accuracy**: Generated queries depend on LLM quality. Some queries may need manual correction.

4. **Performance**: Complex queries may take longer to generate and execute.

## Future Enhancements

- Query history and caching
- Query explanation (why this query was generated)
- Support for write operations (with confirmation)
- Multi-turn conversations (context-aware queries)
- Query optimization suggestions
- Integration with Neo4j Browser

## See Also

- [Neo4j Usage Guide](NEO4J_USAGE.md) - Manual Cypher query examples
- [CLI Usage Guide](CLI_USAGE.md) - Complete CLI reference
- [Graph Schema](neo4j_schema.md) - Detailed schema documentation

