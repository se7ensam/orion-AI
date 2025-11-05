"""
Neo4j Database Connection Module

This module handles connection to Neo4j database (local or Aura Free instance).
"""

import os
from typing import Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    """Manages Neo4j database connection and operations."""
    
    def __init__(self):
        """Initialize Neo4j connection with environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self.driver: Optional[GraphDatabase.driver] = None
    
    def connect(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            self.driver.verify_connectivity()
            print(f"✓ Successfully connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query against Neo4j."""
        if not self.driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def setup_schema(self):
        """Initialize the graph schema with indexes and constraints."""
        print("Setting up Neo4j schema...")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT department_id_unique IF NOT EXISTS FOR (dept:Department) REQUIRE dept.id IS UNIQUE",
            "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
        ]
        
        # Create indexes
        indexes = [
            "CREATE INDEX employee_id IF NOT EXISTS FOR (e:Employee) ON (e.id)",
            "CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id)",
            "CREATE INDEX project_id IF NOT EXISTS FOR (p:Project) ON (p.id)",
            "CREATE INDEX department_id IF NOT EXISTS FOR (dept:Department) ON (dept.id)",
            "CREATE INDEX author_id IF NOT EXISTS FOR (a:Author) ON (a.id)",
            "CREATE INDEX document_file_type IF NOT EXISTS FOR (d:Document) ON (d.file_type)",
        ]
        
        try:
            for constraint in constraints:
                self.execute_query(constraint)
                print(f"  ✓ Created constraint/index")
            
            for index in indexes:
                self.execute_query(index)
                print(f"  ✓ Created index")
            
            print("✓ Schema setup completed successfully")
        except Exception as e:
            print(f"✗ Error setting up schema: {e}")
            raise
    
    def test_connection(self):
        """Test the database connection with a simple query."""
        try:
            result = self.execute_query("RETURN 1 as test")
            if result:
                print("✓ Database connection test successful")
                return True
            return False
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False


def main():
    """Test the Neo4j connection."""
    print("=" * 50)
    print("Neo4j Connection Test")
    print("=" * 50)
    
    conn = Neo4jConnection()
    
    if conn.connect():
        conn.test_connection()
        conn.setup_schema()
        conn.close()
    else:
        print("\nPlease check your .env file and ensure Neo4j is running.")
        print("For Neo4j Aura Free, update NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env")


if __name__ == "__main__":
    main()

