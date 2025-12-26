"""
Cypher RAG Service - Natural Language to Cypher Query Conversion

Uses RAG (Retrieval-Augmented Generation) to convert natural language queries
into Cypher queries for Neo4j graph database.
"""

import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class CypherRAG:
    """RAG service for converting natural language to Cypher queries."""
    
    # Graph schema context for the LLM
    SCHEMA_CONTEXT = """
# Neo4j Graph Schema for SEC EDGAR Filings

## Node Types

### Company
- Properties: id, cik (unique), name, sic_code, sic_description, fiscal_year_end, 
  address_street1, address_city, address_state, address_zip, phone, sec_file_number
- Example: (:Company {cik: "0001234567", name: "Example Corp"})

### Person
- Properties: id (unique), name, title, role_type (CEO, Director, Officer, Signatory, Contact, Executive)
- Example: (:Person {id: "person_john_doe_1234567", name: "John Doe", role_type: "CEO"})

### Event
- Properties: id (unique), event_type (Financial Results, Merger, Acquisition, Restructuring, Filing), 
  title, event_date, filing_id, description
- Example: (:Event {id: "event_123_Acquisition", event_type: "Acquisition", title: "Corporate Acquisition"})

### Sector
- Properties: id, sic_code (unique), name, description
- Example: (:Sector {sic_code: "6029", name: "Commercial Banking"})

## Relationship Types

### OWNS
- Pattern: (:Company)-[:OWNS {ownership_type, acquisition_date?, ownership_percentage?}]->(:Company)
- Meaning: Company A owns Company B

### SUBSIDIARY_OF
- Pattern: (:Company)-[:SUBSIDIARY_OF {ownership_type, acquisition_date?}]->(:Company)
- Meaning: Company A is a subsidiary of Company B

### WORKS_AT
- Pattern: (:Person)-[:WORKS_AT {title, role_type, start_date?, end_date?}]->(:Company)
- Meaning: Person works at Company

### HAS_EVENT
- Pattern: (:Company)-[:HAS_EVENT {event_date, filing_id}]->(:Event)
- Meaning: Company has an Event

### BELONGS_TO_SECTOR
- Pattern: (:Company)-[:BELONGS_TO_SECTOR {sic_code}]->(:Sector)
- Meaning: Company belongs to a Sector

## Common Query Patterns

1. Find companies: MATCH (c:Company) RETURN c.name, c.cik LIMIT 10
2. Find people at a company: MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "Company Name"}) RETURN p.name, p.role_type
3. Find company events: MATCH (c:Company {name: "Company Name"})-[:HAS_EVENT]->(e:Event) RETURN e.event_type, e.title, e.event_date
4. Find ownership chain: MATCH (parent:Company {name: "Parent"})-[:OWNS*]->(sub:Company) RETURN parent.name, sub.name
5. Find companies in sector: MATCH (c:Company)-[:BELONGS_TO_SECTOR]->(s:Sector {sic_code: "6029"}) RETURN c.name
6. Find executives: MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE p.role_type IN ["CEO", "Director", "Officer"] RETURN p.name, c.name

## Important Notes

- Always use MATCH before RETURN
- Use WHERE for filtering conditions
- Use LIMIT to restrict results (default: 10-20)
- Property names are case-sensitive: c.name, c.cik, p.role_type
- Use MERGE for creating nodes, MATCH for querying
- Use relationships like -[:RELATIONSHIP_TYPE]-> for traversing
- Use * for variable-length paths: -[:OWNS*]->
- Use OPTIONAL MATCH for optional relationships
- Use DISTINCT to remove duplicates
- Use ORDER BY for sorting
- Use COUNT(), SUM(), AVG() for aggregations
"""
    
    def __init__(self, model_name: str = "llama3.2", base_url: Optional[str] = None):
        """
        Initialize Cypher RAG service.
        
        Args:
            model_name: Name of the Ollama model to use (default: "llama3.2")
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        self.llm = None
        
        # Ensure model is available
        self._ensure_model_available()
        
        # Initialize LLM
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.1,  # Lower temperature for more consistent queries
                num_ctx=4096  # Larger context for schema understanding
            )
        except Exception as e:
            print(f"Warning: Could not initialize Cypher RAG: {e}")
            self.llm = None
        
        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a Cypher query expert for Neo4j graph databases. 
Your task is to convert natural language questions into valid Cypher queries.

{schema_context}

IMPORTANT RULES:
1. Return ONLY the Cypher query, no explanations or markdown formatting
2. Do not include ```cypher or ``` blocks
3. Use proper Cypher syntax
4. Always include LIMIT when appropriate (default: 20)
5. Use WHERE clauses for filtering
6. Return relevant properties in RETURN clause
7. Handle case-insensitive name matching with toLower() if needed
8. Use OPTIONAL MATCH for relationships that might not exist
9. Always validate the query structure before returning

Example:
User: "Find all companies"
You: MATCH (c:Company) RETURN c.name, c.cik, c.sic_code LIMIT 20

User: "Who works at Apple Inc?"
You: MATCH (p:Person)-[:WORKS_AT]->(c:Company) WHERE toLower(c.name) CONTAINS toLower('Apple Inc') RETURN p.name, p.role_type, p.title, c.name LIMIT 20"""),
            ("human", "{question}")
        ])
        
        self.output_parser = StrOutputParser()
    
    def _ensure_model_available(self):
        """Check if model is available, download if not."""
        try:
            # Check if model exists
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.model_name not in result.stdout:
                print(f"Model {self.model_name} not found. Downloading...")
                subprocess.run(
                    ["ollama", "pull", self.model_name],
                    timeout=300
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Warning: Could not check/download model: {e}")
    
    def is_available(self) -> bool:
        """Check if Cypher RAG is available."""
        return self.llm is not None
    
    def generate_cypher(self, natural_language_query: str) -> str:
        """
        Generate a Cypher query from natural language.
        
        Args:
            natural_language_query: The natural language question
            
        Returns:
            Generated Cypher query string
        """
        if not self.is_available():
            raise RuntimeError("Cypher RAG is not available. Check Ollama connection.")
        
        try:
            # Create the chain
            chain = self.prompt_template | self.llm | self.output_parser
            
            # Generate query
            cypher_query = chain.invoke({
                "schema_context": self.SCHEMA_CONTEXT,
                "question": natural_language_query
            })
            
            # Clean up the query (remove markdown formatting if present)
            cypher_query = cypher_query.strip()
            if cypher_query.startswith("```cypher"):
                cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            elif cypher_query.startswith("```"):
                cypher_query = cypher_query.replace("```", "").strip()
            
            return cypher_query
            
        except Exception as e:
            raise RuntimeError(f"Error generating Cypher query: {e}")
    
    def validate_cypher(self, cypher_query: str) -> tuple:
        """
        Validate a Cypher query syntax (basic validation).
        
        Args:
            cypher_query: The Cypher query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation checks
        query_upper = cypher_query.upper()
        
        # Must contain MATCH or RETURN
        if "MATCH" not in query_upper and "RETURN" not in query_upper:
            return False, "Query must contain MATCH or RETURN clause"
        
        # Check for dangerous operations (CREATE, DELETE, DROP, etc.)
        dangerous_ops = ["CREATE", "DELETE", "DROP", "REMOVE", "SET", "MERGE"]
        for op in dangerous_ops:
            if op in query_upper and "MATCH" not in query_upper:
                return False, f"Query contains {op} without MATCH - this is a write operation"
        
        # Basic syntax checks
        if query_upper.count("MATCH") > 0 and "RETURN" not in query_upper:
            return False, "Query has MATCH but no RETURN clause"
        
        return True, None
    
    def format_results(self, results: List[Dict[str, Any]], max_rows: int = 50) -> str:
        """
        Format query results for display.
        
        Args:
            results: List of result dictionaries from Neo4j
            max_rows: Maximum number of rows to display
            
        Returns:
            Formatted string representation
        """
        if not results:
            return "No results found."
        
        # Limit results
        display_results = results[:max_rows]
        
        # Get all keys from first result
        if not display_results:
            return "No results found."
        
        keys = list(display_results[0].keys())
        
        # Create formatted output
        output_lines = []
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"Results: {len(results)} row(s) found")
        if len(results) > max_rows:
            output_lines.append(f"Showing first {max_rows} rows")
        output_lines.append(f"{'='*80}\n")
        
        # Create table header
        col_widths = {key: max(len(str(key)), max(len(str(row.get(key, ""))) for row in display_results)) for key in keys}
        col_widths = {k: min(v, 40) for k, v in col_widths.items()}  # Cap at 40 chars
        
        # Header
        header = " | ".join(str(key).ljust(col_widths[key]) for key in keys)
        output_lines.append(header)
        output_lines.append("-" * len(header))
        
        # Rows
        for row in display_results:
            row_str = " | ".join(str(row.get(key, "")).ljust(col_widths[key])[:40] for key in keys)
            output_lines.append(row_str)
        
        if len(results) > max_rows:
            output_lines.append(f"\n... and {len(results) - max_rows} more rows")
        
        return "\n".join(output_lines)
    
    def query_with_retry(self, natural_language_query: str, neo4j_conn, max_retries: int = 2) -> tuple[Optional[List[Dict]], Optional[str], str]:
        """
        Execute a natural language query with automatic retry on errors.
        
        Args:
            natural_language_query: The natural language question
            neo4j_conn: Neo4jConnection instance
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (results, error_message, cypher_query)
        """
        cypher_query = None
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Generate Cypher query
                if attempt == 0:
                    cypher_query = self.generate_cypher(natural_language_query)
                else:
                    # On retry, ask LLM to fix the query
                    fix_prompt = f"""The previous Cypher query failed with error: {last_error}

Original question: {natural_language_query}
Previous query: {cypher_query}

Please generate a corrected Cypher query that fixes the error."""
                    cypher_query = self.generate_cypher(fix_prompt)
                
                # Validate query
                is_valid, validation_error = self.validate_cypher(cypher_query)
                if not is_valid:
                    last_error = validation_error
                    if attempt < max_retries:
                        continue
                    return None, validation_error, cypher_query
                
                # Execute query
                results = neo4j_conn.execute_query(cypher_query)
                
                # Convert Neo4j records to dictionaries
                formatted_results = []
                for record in results:
                    # Neo4j Record objects have keys() and values() methods
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert values to strings, handling None and complex types
                        if value is None:
                            record_dict[key] = None
                        elif isinstance(value, (list, dict)):
                            record_dict[key] = str(value)
                        else:
                            record_dict[key] = str(value)
                    formatted_results.append(record_dict)
                
                return formatted_results, None, cypher_query
                
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    print(f"⚠️  Query failed, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                return None, str(e), cypher_query or ""
        
        return None, last_error, cypher_query or ""

