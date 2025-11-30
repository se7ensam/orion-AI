"""
Graph Builder for EDGAR Filings

Extracts entities and relationships from EDGAR filings and builds Neo4j graph.
"""

import re
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime

from src.database.neo4j_connection import Neo4jConnection
from src.data_loader import get_filing_data, list_filings, parse_filing_header


class GraphBuilder:
    """Builds Neo4j graph from EDGAR filings."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize graph builder with Neo4j connection."""
        self.conn = neo4j_conn
        self.processed_companies: Set[str] = set()
        self.processed_people: Set[str] = set()
        self.processed_events: Set[str] = set()
        self.processed_sectors: Set[str] = set()
    
    def format_cik(self, cik: str) -> str:
        """Format CIK to 10-digit zero-padded string."""
        return cik.zfill(10)
    
    def create_company_node(self, company_data: Dict) -> bool:
        """Create or update a Company node."""
        if not company_data.get('cik'):
            return False
        
        cik = self.format_cik(company_data['cik'])
        company_id = f"company_{cik}"
        
        # Prepare properties - keep all, use empty string for missing values
        props = {
            'id': company_id,
            'cik': cik,
            'name': company_data.get('company_name', '').strip() or '',
            'sic_code': company_data.get('sic_code', '') or '',
            'sic_description': company_data.get('sic_description', '') or '',
            'fiscal_year_end': company_data.get('fiscal_year_end', '') or '',
            'address_street1': company_data.get('address_street1', '') or '',
            'address_city': company_data.get('address_city', '') or '',
            'address_state': company_data.get('address_state', '') or '',
            'address_zip': company_data.get('address_zip', '') or '',
            'phone': company_data.get('phone', '') or '',
            'sec_file_number': company_data.get('sec_file_number', '') or '',
        }
        
        # Create or update company - only set non-empty properties
        # Use COALESCE to handle empty strings as NULL
        query = """
        MERGE (c:Company {cik: $cik})
        SET c.id = $id,
            c.name = COALESCE(NULLIF($name, ''), c.name),
            c.sic_code = COALESCE(NULLIF($sic_code, ''), c.sic_code),
            c.sic_description = COALESCE(NULLIF($sic_description, ''), c.sic_description),
            c.fiscal_year_end = COALESCE(NULLIF($fiscal_year_end, ''), c.fiscal_year_end),
            c.address_street1 = COALESCE(NULLIF($address_street1, ''), c.address_street1),
            c.address_city = COALESCE(NULLIF($address_city, ''), c.address_city),
            c.address_state = COALESCE(NULLIF($address_state, ''), c.address_state),
            c.address_zip = COALESCE(NULLIF($address_zip, ''), c.address_zip),
            c.phone = COALESCE(NULLIF($phone, ''), c.phone),
            c.sec_file_number = COALESCE(NULLIF($sec_file_number, ''), c.sec_file_number)
        RETURN c
        """
        
        try:
            self.conn.execute_query(query, props)
            self.processed_companies.add(cik)
            return True
        except Exception as e:
            print(f"Error creating company node: {e}")
            return False
    
    def create_sector_node(self, sic_code: str, sic_description: str) -> bool:
        """Create or update a Sector node."""
        if not sic_code:
            return False
        
        sector_id = f"sector_{sic_code}"
        
        if sector_id in self.processed_sectors:
            return True
        
        query = """
        MERGE (s:Sector {sic_code: $sic_code})
        SET s.id = $id,
            s.name = $name,
            s.description = $description
        RETURN s
        """
        
        props = {
            'id': sector_id,
            'sic_code': sic_code,
            'name': sic_description or f"SIC {sic_code}",
            'description': sic_description or ''
        }
        
        try:
            self.conn.execute_query(query, props)
            self.processed_sectors.add(sector_id)
            return True
        except Exception as e:
            print(f"Error creating sector node: {e}")
            return False
    
    def create_company_sector_relationship(self, cik: str, sic_code: str) -> bool:
        """Create BELONGS_TO_SECTOR relationship."""
        if not cik or not sic_code:
            return False
        
        cik = self.format_cik(cik)
        
        query = """
        MATCH (c:Company {cik: $cik})
        MATCH (s:Sector {sic_code: $sic_code})
        MERGE (c)-[r:BELONGS_TO_SECTOR]->(s)
        SET r.sic_code = $sic_code
        RETURN r
        """
        
        try:
            self.conn.execute_query(query, {'cik': cik, 'sic_code': sic_code})
            return True
        except Exception as e:
            print(f"Error creating sector relationship: {e}")
            return False
    
    def extract_people_from_filing(self, filing_data: Dict) -> List[Dict]:
        """Extract people (executives, directors, signatories) from filing."""
        people = []
        content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
        
        if not content:
            return people
        
        # Pattern 1: Signatures section
        signature_pattern = r'By\s*/\s*s\s*/\s*([A-Z][a-zA-Z\s\-\.]+)'
        signature_matches = re.finditer(signature_pattern, content, re.IGNORECASE)
        for match in signature_matches:
            name = match.group(1).strip()
            # Clean up name
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 3 and name not in ['Authorised Signatory', 'Signatory']:
                people.append({
                    'name': name,
                    'title': 'Authorised Signatory',
                    'role_type': 'Signatory'
                })
        
        # Pattern 2: Contacts section (table format)
        # Look for patterns like "Name (Title, Company)"
        contact_pattern = r'([A-Z][a-zA-Z\s\-\.]+)\s*\(([^)]+)\)'
        contact_matches = re.finditer(contact_pattern, content)
        for match in contact_matches:
            name = match.group(1).strip()
            title_info = match.group(2).strip()
            
            # Extract title
            title = title_info.split(',')[0].strip()
            
            people.append({
                'name': name,
                'title': title,
                'role_type': self._classify_role(title)
            })
        
        # Pattern 3: Chief Executive, CEO mentions
        ceo_patterns = [
            r'Chief Executive[:\s]+([A-Z][a-zA-Z\s\-\.]+)',
            r'CEO[:\s]+([A-Z][a-zA-Z\s\-\.]+)',
            r'([A-Z][a-zA-Z\s\-\.]+),\s*Chief Executive',
        ]
        
        for pattern in ceo_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if len(name) > 3:
                    people.append({
                        'name': name,
                        'title': 'Chief Executive',
                        'role_type': 'CEO'
                    })
        
        # Pattern 4: Director mentions
        director_pattern = r'([A-Z][a-zA-Z\s\-\.]+)\s*\(([^)]*Director[^)]*)\)'
        director_matches = re.finditer(director_pattern, content, re.IGNORECASE)
        for match in director_matches:
            name = match.group(1).strip()
            title = match.group(2).strip()
            people.append({
                'name': name,
                'title': title,
                'role_type': 'Director'
            })
        
        # Deduplicate by name
        seen = set()
        unique_people = []
        for person in people:
            name_key = person['name'].lower()
            if name_key not in seen:
                seen.add(name_key)
                unique_people.append(person)
        
        return unique_people
    
    def _classify_role(self, title: str) -> str:
        """Classify a job title into a role type."""
        title_lower = title.lower()
        
        if 'chief executive' in title_lower or 'ceo' in title_lower:
            return 'CEO'
        elif 'director' in title_lower:
            return 'Director'
        elif 'officer' in title_lower:
            return 'Officer'
        elif 'signatory' in title_lower:
            return 'Signatory'
        elif 'contact' in title_lower or 'relations' in title_lower:
            return 'Contact'
        else:
            return 'Executive'
    
    def create_person_node(self, person_data: Dict, company_cik: str) -> bool:
        """Create or update a Person node."""
        if not person_data.get('name'):
            return False
        
        name = person_data['name'].strip()
        person_id = f"person_{name.lower().replace(' ', '_')}_{company_cik}"
        
        if person_id in self.processed_people:
            return True
        
        query = """
        MERGE (p:Person {id: $id})
        SET p.name = $name,
            p.title = $title,
            p.role_type = $role_type
        RETURN p
        """
        
        props = {
            'id': person_id,
            'name': name,
            'title': person_data.get('title', ''),
            'role_type': person_data.get('role_type', 'Executive')
        }
        
        try:
            self.conn.execute_query(query, props)
            self.processed_people.add(person_id)
            return True
        except Exception as e:
            print(f"Error creating person node: {e}")
            return False
    
    def create_works_at_relationship(self, person_name: str, company_cik: str, person_data: Dict) -> bool:
        """Create WORKS_AT relationship."""
        if not person_name or not company_cik:
            return False
        
        company_cik = self.format_cik(company_cik)
        person_id = f"person_{person_name.lower().replace(' ', '_')}_{company_cik}"
        
        query = """
        MATCH (p:Person {id: $person_id})
        MATCH (c:Company {cik: $company_cik})
        MERGE (p)-[r:WORKS_AT]->(c)
        SET r.title = $title,
            r.role_type = $role_type
        RETURN r
        """
        
        props = {
            'person_id': person_id,
            'company_cik': company_cik,
            'title': person_data.get('title', ''),
            'role_type': person_data.get('role_type', 'Executive')
        }
        
        try:
            self.conn.execute_query(query, props)
            return True
        except Exception as e:
            print(f"Error creating WORKS_AT relationship: {e}")
            return False
    
    def extract_companies_from_filing(self, filing_data: Dict) -> List[Dict]:
        """Extract mentioned companies from filing content."""
        companies = []
        content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
        
        if not content:
            return companies
        
        # Look for company mentions (capitalized, multi-word names)
        # Pattern: Company names often appear in quotes or after "of", "by", etc.
        company_patterns = [
            r'([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP|SA|S\.A\.|N\.V\.))',
            r'([A-Z][A-Za-z\s&\.]+)\s+(?:plc|ltd|inc|corp|sa|s\.a\.|n\.v\.)',
        ]
        
        seen = set()
        for pattern in company_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                company_name = match.group(1).strip()
                # Filter out common false positives
                if (len(company_name) > 3 and 
                    company_name not in ['SEC', 'SECURITIES', 'EXCHANGE', 'COMMISSION'] and
                    company_name.lower() not in seen):
                    seen.add(company_name.lower())
                    companies.append({'name': company_name})
        
        return companies
    
    def extract_ownership_relationships(self, filing_data: Dict, primary_company_cik: str) -> List[Dict]:
        """Extract ownership/subsidiary relationships from filing."""
        relationships = []
        content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
        
        if not content:
            return relationships
        
        # Pattern 1: "Company A owns Company B"
        owns_pattern = r'([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)\s+(?:owns|acquired|purchased)\s+([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)'
        
        # Pattern 2: "subsidiary of"
        subsidiary_pattern = r'([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)\s+is\s+(?:a\s+)?subsidiary\s+of\s+([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)'
        
        # Pattern 3: "parent company"
        parent_pattern = r'([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)\s+is\s+(?:the\s+)?parent\s+company\s+of\s+([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)'
        
        # Pattern 4: "wholly owned"
        wholly_owned_pattern = r'([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)\s+is\s+(?:a\s+)?wholly\s+owned\s+subsidiary\s+of\s+([A-Z][A-Za-z\s&\.]+(?:PLC|LTD|INC|CORP)?)'
        
        patterns = [
            (owns_pattern, 'OWNS'),
            (subsidiary_pattern, 'SUBSIDIARY_OF'),
            (parent_pattern, 'OWNS'),  # Reverse relationship
            (wholly_owned_pattern, 'SUBSIDIARY_OF')
        ]
        
        for pattern, rel_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if rel_type == 'OWNS':
                    parent = match.group(1).strip()
                    child = match.group(2).strip()
                else:  # SUBSIDIARY_OF
                    child = match.group(1).strip()
                    parent = match.group(2).strip()
                
                relationships.append({
                    'parent_company': parent,
                    'child_company': child,
                    'relationship_type': rel_type,
                    'ownership_type': 'wholly owned' if 'wholly' in match.group(0).lower() else 'unknown'
                })
        
        return relationships
    
    def create_ownership_relationship(self, parent_cik: str, child_cik: str, rel_data: Dict) -> bool:
        """Create OWNS or SUBSIDIARY_OF relationship."""
        if not parent_cik or not child_cik:
            return False
        
        parent_cik = self.format_cik(parent_cik)
        child_cik = self.format_cik(child_cik)
        
        rel_type = rel_data.get('relationship_type', 'OWNS')
        
        if rel_type == 'OWNS':
            query = """
            MATCH (parent:Company {cik: $parent_cik})
            MATCH (child:Company {cik: $child_cik})
            MERGE (parent)-[r:OWNS]->(child)
            SET r.ownership_type = $ownership_type
            RETURN r
            """
        else:  # SUBSIDIARY_OF
            query = """
            MATCH (child:Company {cik: $child_cik})
            MATCH (parent:Company {cik: $parent_cik})
            MERGE (child)-[r:SUBSIDIARY_OF]->(parent)
            SET r.ownership_type = $ownership_type
            RETURN r
            """
        
        props = {
            'parent_cik': parent_cik,
            'child_cik': child_cik,
            'ownership_type': rel_data.get('ownership_type', 'unknown')
        }
        
        try:
            self.conn.execute_query(query, props)
            return True
        except Exception as e:
            print(f"Error creating ownership relationship: {e}")
            return False
    
    def extract_events_from_filing(self, filing_data: Dict) -> List[Dict]:
        """Extract events from filing."""
        events = []
        
        accession = filing_data.get('accession_number', '')
        filing_date = filing_data.get('filing_date', '')
        content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
        
        if not accession:
            return events
        
        # Determine event type from content
        content_lower = content.lower()
        
        event_type = 'Filing'
        title = f"6-K Filing {accession}"
        
        if 'quarterly' in content_lower or 'q1' in content_lower or 'q2' in content_lower:
            event_type = 'Financial Results'
            # Try to extract quarter info
            q_match = re.search(r'Q([1-4])\s*(\d{4})', content, re.IGNORECASE)
            if q_match:
                title = f"Q{q_match.group(1)} {q_match.group(2)} Results"
        
        elif 'merger' in content_lower or 'combine' in content_lower:
            event_type = 'Merger'
            # Extract merger title
            merger_match = re.search(r'([Mm]erger|[Cc]ombination)\s+(?:of|between)\s+([A-Z][A-Za-z\s&\.]+)', content)
            if merger_match:
                title = f"{merger_match.group(1)} - {merger_match.group(2)}"
        
        elif 'acquisition' in content_lower or 'acquired' in content_lower:
            event_type = 'Acquisition'
            title = "Corporate Acquisition"
        
        elif 'restructuring' in content_lower or 'legal structure' in content_lower:
            event_type = 'Restructuring'
            title = "Corporate Restructuring"
        
        event_id = f"event_{accession}_{event_type}"
        
        if event_id not in self.processed_events:
            events.append({
                'id': event_id,
                'event_type': event_type,
                'title': title,
                'event_date': filing_date,
                'filing_id': accession,
                'description': content[:500] if content else ''  # First 500 chars
            })
            self.processed_events.add(event_id)
        
        return events
    
    def create_event_node(self, event_data: Dict) -> bool:
        """Create or update an Event node."""
        if not event_data.get('id'):
            return False
        
        query = """
        MERGE (e:Event {id: $id})
        SET e.event_type = $event_type,
            e.title = $title,
            e.event_date = $event_date,
            e.filing_id = $filing_id,
            e.description = $description
        RETURN e
        """
        
        props = {
            'id': event_data['id'],
            'event_type': event_data.get('event_type', 'Filing'),
            'title': event_data.get('title', ''),
            'event_date': event_data.get('event_date', ''),
            'filing_id': event_data.get('filing_id', ''),
            'description': event_data.get('description', '')
        }
        
        try:
            self.conn.execute_query(query, props)
            return True
        except Exception as e:
            print(f"Error creating event node: {e}")
            return False
    
    def create_has_event_relationship(self, company_cik: str, event_id: str, filing_date: str) -> bool:
        """Create HAS_EVENT relationship."""
        if not company_cik or not event_id:
            return False
        
        company_cik = self.format_cik(company_cik)
        
        query = """
        MATCH (c:Company {cik: $company_cik})
        MATCH (e:Event {id: $event_id})
        MERGE (c)-[r:HAS_EVENT]->(e)
        SET r.event_date = $filing_date,
            r.filing_id = $filing_id
        RETURN r
        """
        
        props = {
            'company_cik': company_cik,
            'event_id': event_id,
            'filing_date': filing_date,
            'filing_id': event_id.split('_')[1] if '_' in event_id else ''
        }
        
        try:
            self.conn.execute_query(query, props)
            return True
        except Exception as e:
            print(f"Error creating HAS_EVENT relationship: {e}")
            return False
    
    def process_filing(self, filing_path: Path) -> Dict[str, int]:
        """
        Process a single filing and extract all entities/relationships.
        
        Returns:
            Dictionary with counts of created entities/relationships
        """
        stats = {
            'companies': 0,
            'people': 0,
            'events': 0,
            'relationships': 0
        }
        
        try:
            # Load filing data
            filing_data = get_filing_data(filing_path)
            
            if not filing_data.get('cik'):
                return stats
            
            company_cik = filing_data['cik']
            
            # 1. Create company node
            if self.create_company_node(filing_data):
                stats['companies'] += 1
            
            # 2. Create sector node and relationship
            sic_code = filing_data.get('sic_code')
            sic_description = filing_data.get('sic_description', '')
            if sic_code:
                if self.create_sector_node(sic_code, sic_description):
                    if self.create_company_sector_relationship(company_cik, sic_code):
                        stats['relationships'] += 1
            
            # 3. Extract and create people
            people = self.extract_people_from_filing(filing_data)
            for person_data in people:
                if self.create_person_node(person_data, company_cik):
                    stats['people'] += 1
                if self.create_works_at_relationship(person_data['name'], company_cik, person_data):
                    stats['relationships'] += 1
            
            # 4. Extract and create events
            events = self.extract_events_from_filing(filing_data)
            for event_data in events:
                if self.create_event_node(event_data):
                    stats['events'] += 1
                if self.create_has_event_relationship(company_cik, event_data['id'], filing_data.get('filing_date', '')):
                    stats['relationships'] += 1
            
            # 5. Extract ownership relationships (basic - would need CIK lookup for full implementation)
            # For now, we'll create company nodes for mentioned companies but relationships need CIK lookup
            
        except Exception as e:
            print(f"Error processing filing {filing_path}: {e}")
        
        return stats
    
    def process_filings(self, year: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Process multiple filings.
        
        Args:
            year: Optional year filter
            limit: Optional limit on number of filings to process
            
        Returns:
            Dictionary with total counts
        """
        filings = list_filings(year)
        
        if limit:
            filings = filings[:limit]
        
        total_stats = {
            'companies': 0,
            'people': 0,
            'events': 0,
            'relationships': 0,
            'filings_processed': 0
        }
        
        print(f"Processing {len(filings)} filings...")
        
        for i, filing_path in enumerate(filings, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(filings)} filings...")
            
            stats = self.process_filing(filing_path)
            
            for key in total_stats:
                if key in stats:
                    total_stats[key] += stats[key]
            
            total_stats['filings_processed'] += 1
        
        return total_stats


if __name__ == "__main__":
    # Test the graph builder
    print("Testing Graph Builder")
    print("=" * 50)
    
    conn = Neo4jConnection()
    if conn.connect():
        conn.setup_schema()
        
        builder = GraphBuilder(conn)
        
        # Process a few test filings
        print("\nProcessing test filings...")
        stats = builder.process_filings(year=2009, limit=5)
        
        print(f"\nResults:")
        print(f"  Companies: {stats['companies']}")
        print(f"  People: {stats['people']}")
        print(f"  Events: {stats['events']}")
        print(f"  Relationships: {stats['relationships']}")
        print(f"  Filings Processed: {stats['filings_processed']}")
        
        conn.close()
    else:
        print("Failed to connect to Neo4j")

