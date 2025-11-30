# Neo4j Usage Guide

## Overview

This guide explains how to use Neo4j with the Orion project to build a graph database from EDGAR filings.

---

## Quick Start

### 1. Start Neo4j

**Option A: Using Docker Compose (Recommended)**

```bash
# From project root - using Makefile
make neo4j

# Or using docker-compose directly
docker-compose up -d neo4j
```

This will start Neo4j on:
- **HTTP**: http://localhost:7474 (Browser UI)
- **Bolt**: bolt://localhost:7687 (Application connection)

**Default credentials:**
- Username: `neo4j`
- Password: `orion123` (or set `NEO4J_PASSWORD` in `.env`)

**Note**: Neo4j is in the main `docker-compose.yml` file alongside the download service for unified management.

**Option B: Using Neo4j Desktop or Aura**

1. Install Neo4j Desktop or create a Neo4j Aura instance
2. Update `.env` with your connection details:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

---

### 2. Setup Schema

Initialize the Neo4j schema with indexes and constraints:

```bash
python -m src.cli setup-db
```

This creates:
- Node types: `Company`, `Person`, `Event`, `Sector`, `Rating`, `Debenture`
- Relationships: `OWNS`, `SUBSIDIARY_OF`, `WORKS_AT`, `HAS_EVENT`, `BELONGS_TO_SECTOR`, `RATED_BY`
- Indexes and constraints for performance

---

### 3. Load Filings into Graph

Process EDGAR filings and build the graph:

```bash
# Process all filings from 2009
python -m src.cli load-graph --year 2009

# Process with limit (for testing)
python -m src.cli load-graph --year 2009 --limit 10

# Process all years (no year filter)
python -m src.cli load-graph

# Skip schema setup (if already done)
python -m src.cli load-graph --year 2009 --skip-schema
```

---

## Graph Schema

### Node Types

#### Company
```cypher
(:Company) {
  id: string,
  cik: string (unique),
  name: string,
  sic_code: string,
  sic_description: string,
  fiscal_year_end: string,
  address_street1: string,
  address_city: string,
  address_state: string,
  address_zip: string,
  phone: string,
  sec_file_number: string
}
```

#### Person
```cypher
(:Person) {
  id: string (unique),
  name: string,
  title: string,
  role_type: string (CEO, Director, Officer, Signatory, Contact, Executive)
}
```

#### Event
```cypher
(:Event) {
  id: string (unique),
  event_type: string (Financial Results, Merger, Acquisition, Restructuring, Filing),
  title: string,
  event_date: date,
  filing_id: string,
  description: string
}
```

#### Sector
```cypher
(:Sector) {
  id: string,
  sic_code: string (unique),
  name: string,
  description: string
}
```

### Relationship Types

#### OWNS
```cypher
(:Company)-[:OWNS {
  ownership_type: string,
  acquisition_date: date (optional),
  ownership_percentage: float (optional)
}]->(:Company)
```

#### SUBSIDIARY_OF
```cypher
(:Company)-[:SUBSIDIARY_OF {
  ownership_type: string,
  acquisition_date: date (optional)
}]->(:Company)
```

#### WORKS_AT
```cypher
(:Person)-[:WORKS_AT {
  title: string,
  role_type: string,
  start_date: date (optional),
  end_date: date (optional)
}]->(:Company)
```

#### HAS_EVENT
```cypher
(:Company)-[:HAS_EVENT {
  event_date: date,
  filing_id: string
}]->(:Event)
```

#### BELONGS_TO_SECTOR
```cypher
(:Company)-[:BELONGS_TO_SECTOR {
  sic_code: string
}]->(:Sector)
```

---

## Example Queries

### Find All Companies
```cypher
MATCH (c:Company)
RETURN c.name, c.cik, c.sic_code
LIMIT 10;
```

### Find Executives at a Company
```cypher
MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "ABBEY NATIONAL PLC"})
WHERE p.role_type IN ["CEO", "Director", "Officer"]
RETURN p.name, p.title, p.role_type;
```

### Find Company Ownership Chain
```cypher
MATCH (parent:Company {name: "Banco Santander, S.A."})-[:OWNS*]->(sub:Company)
RETURN parent.name, sub.name;
```

### Find All Events for a Company
```cypher
MATCH (c:Company {name: "ABBEY NATIONAL PLC"})-[:HAS_EVENT]->(e:Event)
RETURN e.event_type, e.title, e.event_date
ORDER BY e.event_date DESC;
```

### Find Companies in a Sector
```cypher
MATCH (c:Company)-[:BELONGS_TO_SECTOR]->(s:Sector {sic_code: "6029"})
RETURN c.name, c.cik
LIMIT 20;
```

### Find Merger/Acquisition Events
```cypher
MATCH (c:Company)-[:HAS_EVENT]->(e:Event)
WHERE e.event_type IN ["Merger", "Acquisition"]
RETURN c.name, e.title, e.event_date
ORDER BY e.event_date DESC;
```

### Count Entities
```cypher
MATCH (c:Company)
WITH count(c) as companies
MATCH (p:Person)
WITH companies, count(p) as people
MATCH (e:Event)
RETURN companies, people, count(e) as events;
```

---

## Accessing Neo4j Browser

1. Start Neo4j: `cd neo4j && docker-compose up -d`
2. Open browser: http://localhost:7474
3. Login with:
   - Username: `neo4j`
   - Password: `orion123` (or your `.env` password)
4. Run queries in the Cypher query editor

---

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to Neo4j"**

1. Check if Neo4j is running:
   ```bash
   docker-compose ps neo4j
   # Or
   make status
   ```

2. Check `.env` file has correct credentials:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=orion123
   ```

3. Test connection:
   ```bash
   python -m src.cli test-db --neo4j
   ```

### Schema Issues

**Error: "Constraint already exists"**

- This is normal if schema was already set up
- Use `--skip-schema` flag when loading graph

### Performance Issues

**Slow queries:**

1. Check indexes are created:
   ```cypher
   SHOW INDEXES;
   ```

2. Use `LIMIT` in queries for testing

3. For large datasets, process in batches:
   ```bash
   python -m src.cli load-graph --year 2009 --limit 100
   ```

---

## Next Steps

1. **Query the Graph**: Use Neo4j Browser or Cypher queries
2. **Build RAG Pipeline**: Combine graph queries with vector search
3. **Add More Relationships**: Extend `graph_builder.py` to extract more entity types
4. **Visualize**: Use Neo4j Browser's visualization features

---

## Files Created

- `src/database/neo4j_connection.py` - Updated with EDGAR schema
- `src/data_loader.py` - Loads and parses EDGAR filings
- `src/graph_builder.py` - Extracts entities and builds graph
- `neo4j/docker-compose.yml` - Neo4j Docker configuration
- `neo4j/seed.cypher` - Sample queries and examples

