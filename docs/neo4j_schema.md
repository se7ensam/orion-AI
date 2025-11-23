# Neo4j Graph Schema

## Overview
This document defines the graph schema for the document management and knowledge graph system.

## Node Types

### Employee
Represents an employee in the organization.
- **Properties:**
  - `id`: String (unique identifier)
  - `name`: String
  - `email`: String
  - `department`: String
  - `role`: String
  - `created_at`: DateTime
  - `updated_at`: DateTime

### Document
Represents a document in the system.
- **Properties:**
  - `id`: String (unique identifier)
  - `title`: String
  - `content`: String (full text content)
  - `file_path`: String
  - `file_type`: String (pdf, docx, txt, etc.)
  - `file_size`: Integer (bytes)
  - `created_at`: DateTime
  - `updated_at`: DateTime
  - `metadata`: Map (additional metadata)

### Project
Represents a project in the organization.
- **Properties:**
  - `id`: String (unique identifier)
  - `name`: String
  - `description`: String
  - `status`: String (active, completed, archived)
  - `start_date`: Date
  - `end_date`: Date
  - `created_at`: DateTime
  - `updated_at`: DateTime

### Department
Represents a department in the organization.
- **Properties:**
  - `id`: String (unique identifier)
  - `name`: String
  - `description`: String
  - `created_at`: DateTime
  - `updated_at`: DateTime

### Author
Represents an author of a document (can be an employee or external author).
- **Properties:**
  - `id`: String (unique identifier)
  - `name`: String
  - `email`: String (optional)
  - `type`: String (internal, external)
  - `created_at`: DateTime

## Relationship Types

### WORKED_ON
- **From:** Employee
- **To:** Document
- **Properties:**
  - `role`: String (creator, editor, reviewer, etc.)
  - `start_date`: Date
  - `end_date`: Date (optional)
  - `created_at`: DateTime

### BELONGS_TO
- **From:** Document
- **To:** Project
- **Properties:**
  - `created_at`: DateTime
  - `category`: String (optional)

### WROTE
- **From:** Author
- **To:** Document
- **Properties:**
  - `created_at`: DateTime
  - `contribution_type`: String (primary, co-author, contributor)

### PART_OF
- **From:** Project
- **To:** Department
- **Properties:**
  - `created_at`: DateTime

### MEMBER_OF
- **From:** Employee
- **To:** Department
- **Properties:**
  - `role`: String (manager, member, lead)
  - `start_date`: Date
  - `end_date`: Date (optional)
  - `created_at`: DateTime

## Graph Schema Diagram

```
(Employee) -[:WORKED_ON {role, start_date}]-> (Document)
(Author) -[:WROTE {contribution_type}]-> (Document)
(Document) -[:BELONGS_TO {category}]-> (Project)
(Project) -[:PART_OF]-> (Department)
(Employee) -[:MEMBER_OF {role}]-> (Department)
```

## Indexes

### Recommended Indexes
```cypher
CREATE INDEX employee_id IF NOT EXISTS FOR (e:Employee) ON (e.id);
CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id);
CREATE INDEX project_id IF NOT EXISTS FOR (p:Project) ON (p.id);
CREATE INDEX department_id IF NOT EXISTS FOR (dept:Department) ON (dept.id);
CREATE INDEX author_id IF NOT EXISTS FOR (a:Author) ON (a.id);

CREATE FULLTEXT INDEX document_title IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content];
CREATE INDEX document_file_type IF NOT EXISTS FOR (d:Document) ON (d.file_type);
```

## Constraints

### Recommended Constraints
```cypher
CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT department_id_unique IF NOT EXISTS FOR (dept:Department) REQUIRE dept.id IS UNIQUE;
CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE;
```

