// Neo4j Seed Data and Example Queries
// This file contains sample Cypher queries for testing and exploring the graph

// ============================================================================
// SAMPLE QUERIES FOR EXPLORATION
// ============================================================================

// 1. Find all companies
MATCH (c:Company)
RETURN c.name, c.cik, c.sic_code
LIMIT 10;

// 2. Find all people and their companies
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
RETURN p.name, p.title, c.name
LIMIT 20;

// 3. Find all events for a specific company
MATCH (c:Company {name: "ABBEY NATIONAL PLC"})-[:HAS_EVENT]->(e:Event)
RETURN e.event_type, e.title, e.event_date
ORDER BY e.event_date DESC;

// 4. Find company ownership hierarchy
MATCH (parent:Company)-[:OWNS]->(child:Company)
RETURN parent.name, child.name
LIMIT 20;

// 5. Find subsidiaries of a company
MATCH (parent:Company {name: "Banco Santander, S.A."})-[:OWNS*]->(sub:Company)
RETURN sub.name, sub.cik;

// 6. Find all companies in a sector
MATCH (c:Company)-[:BELONGS_TO_SECTOR]->(s:Sector {sic_code: "6029"})
RETURN c.name, c.cik
LIMIT 20;

// 7. Find executives at a company
MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "ABBEY NATIONAL PLC"})
WHERE p.role_type IN ["CEO", "Director", "Officer"]
RETURN p.name, p.title, p.role_type;

// 8. Find all merger/acquisition events
MATCH (c:Company)-[:HAS_EVENT]->(e:Event)
WHERE e.event_type IN ["Merger", "Acquisition"]
RETURN c.name, e.title, e.event_date
ORDER BY e.event_date DESC;

// 9. Find financial results events
MATCH (c:Company)-[:HAS_EVENT]->(e:Event)
WHERE e.event_type = "Financial Results"
RETURN c.name, e.title, e.event_date
ORDER BY e.event_date DESC
LIMIT 20;

// 10. Count entities by type
MATCH (c:Company)
WITH count(c) as companies
MATCH (p:Person)
WITH companies, count(p) as people
MATCH (e:Event)
WITH companies, people, count(e) as events
MATCH (s:Sector)
RETURN companies, people, events, count(s) as sectors;

// 11. Find most connected companies (by relationships)
MATCH (c:Company)
OPTIONAL MATCH (c)-[r1:OWNS]->()
OPTIONAL MATCH ()-[r2:SUBSIDIARY_OF]->(c)
OPTIONAL MATCH (c)-[r3:HAS_EVENT]->()
OPTIONAL MATCH ()-[r4:WORKS_AT]->(c)
WITH c, count(DISTINCT r1) + count(DISTINCT r2) + count(DISTINCT r3) + count(DISTINCT r4) as connections
WHERE connections > 0
RETURN c.name, connections
ORDER BY connections DESC
LIMIT 10;

// 12. Find people who work at multiple companies (if any)
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WITH p, collect(DISTINCT c.name) as companies
WHERE size(companies) > 1
RETURN p.name, companies;

// ============================================================================
// DATA CLEANUP QUERIES (Use with caution!)
// ============================================================================

// Delete all nodes and relationships (WARNING: This deletes everything!)
// MATCH (n) DETACH DELETE n;

// Delete only test data
// MATCH (c:Company)
// WHERE c.name CONTAINS "TEST"
// DETACH DELETE c;

// ============================================================================
// INDEX AND CONSTRAINT CREATION (Already in setup_schema, but for reference)
// ============================================================================

// Constraints
// CREATE CONSTRAINT company_cik_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.cik IS UNIQUE;
// CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
// CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
// CREATE CONSTRAINT sector_sic_unique IF NOT EXISTS FOR (s:Sector) REQUIRE s.sic_code IS UNIQUE;

// Indexes
// CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name);
// CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
// CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.event_date);

