"""
Neo4j Database Connection Module

This module handles connection to Neo4j database (local or Aura Free instance).
"""

import os
import logging
from typing import Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class Neo4jConnection:
    """Manages Neo4j database connection and operations."""
    
    def __init__(self):
        """Initialize Neo4j connection with environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        # Default password matches docker-compose.yml default
        self.password = os.getenv("NEO4J_PASSWORD", "orion123")
        self.driver: Optional[GraphDatabase.driver] = None
    
    def connect(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            # Ensure password is not empty
            if not self.password:
                self.password = "orion123"  # Default from docker-compose
            
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            # Verify connection
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            logger.debug(f"URI: {self.uri}")
            logger.debug(f"User: {self.user}")
            logger.debug(f"Password set: {'Yes' if self.password else 'No'}")
            return False
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query against Neo4j."""
        if not self.driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def setup_schema(self):
        """Initialize the graph schema with indexes and constraints for EDGAR filings."""
        logger.info("Setting up Neo4j schema for EDGAR filings...")
        
        # Create constraints for EDGAR entities
        constraints = [
            # Company constraints
            "CREATE CONSTRAINT company_cik_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.cik IS UNIQUE",
            "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
            
            # Person constraints
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            
            # Event constraints
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            
            # Sector constraints
            "CREATE CONSTRAINT sector_sic_unique IF NOT EXISTS FOR (s:Sector) REQUIRE s.sic_code IS UNIQUE",
            
            # Rating constraints
            "CREATE CONSTRAINT rating_id_unique IF NOT EXISTS FOR (r:Rating) REQUIRE r.id IS UNIQUE",
            
            # Debenture constraints (optional)
            "CREATE CONSTRAINT debenture_id_unique IF NOT EXISTS FOR (d:Debenture) REQUIRE d.id IS UNIQUE",
        ]
        
        # Create indexes for performance
        indexes = [
            # Company indexes
            "CREATE INDEX company_cik IF NOT EXISTS FOR (c:Company) ON (c.cik)",
            "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX company_sic_code IF NOT EXISTS FOR (c:Company) ON (c.sic_code)",
            
            # Person indexes
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX person_role_type IF NOT EXISTS FOR (p:Person) ON (p.role_type)",
            
            # Event indexes
            "CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.event_type)",
            "CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.event_date)",
            "CREATE INDEX event_filing_id IF NOT EXISTS FOR (e:Event) ON (e.filing_id)",
            
            # Sector indexes
            "CREATE INDEX sector_sic_code IF NOT EXISTS FOR (s:Sector) ON (s.sic_code)",
            
            # Rating indexes
            "CREATE INDEX rating_agency IF NOT EXISTS FOR (r:Rating) ON (r.rating_agency)",
            "CREATE INDEX rating_date IF NOT EXISTS FOR (r:Rating) ON (r.rating_date)",
        ]
        
        try:
            logger.info("Creating constraints...")
            for constraint in constraints:
                try:
                    self.execute_query(constraint)
                    logger.info("Created constraint")
                except Exception as e:
                    # Some constraints might already exist, continue
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Constraint warning: {e}")
            
            logger.info("Creating indexes...")
            for index in indexes:
                try:
                    self.execute_query(index)
                    logger.info("Created index")
                except Exception as e:
                    # Some indexes might already exist, continue
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Index warning: {e}")
            
            logger.info("Schema setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up schema: {e}")
            raise
    
    def test_connection(self):
        """Test the database connection with a simple query."""
        try:
            result = self.execute_query("RETURN 1 as test")
            if result:
                logger.info("Database connection test successful")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def main():
    """Test the Neo4j connection."""
    logger.info("=" * 50)
    logger.info("Neo4j Connection Test")
    logger.info("=" * 50)
    
    conn = Neo4jConnection()
    
    if conn.connect():
        conn.test_connection()
        conn.setup_schema()
        conn.close()
    else:
        logger.error("Please check your .env file and ensure Neo4j is running.")
        logger.error("For Neo4j Aura Free, update NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env")


if __name__ == "__main__":
    main()

