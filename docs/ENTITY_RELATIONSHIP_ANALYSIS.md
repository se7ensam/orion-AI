# Entity Relationship Analysis - EDGAR 6-K Filings (2009-2010)

## Executive Summary

Analysis of **1,814 filings** from 2009-2010 reveals consistent patterns of entity relationships across EDGAR 6-K filings. This document identifies the **most valuable entity relationships** for building a comprehensive graph database.

---

## Dataset Overview

- **Total Filings Analyzed**: 1,814
- **Years Covered**: 2009-2010
- **Form Type**: 6-K (Report of Foreign Issuer)
- **Companies**: Multiple Foreign Private Issuers (FPIs)

### Pattern Frequency Analysis

| Pattern Type | Files with Pattern | Frequency |
|-------------|-------------------|-----------|
| **Executives/Directors** | 706 files | 12,741 mentions |
| **Subsidiaries/Acquisitions** | 304 files | 6,052 mentions |
| **Financial Events** | ~500+ files | Very common |
| **Mergers/Combinations** | ~50+ files | Moderate |
| **Ratings** | ~100+ files | Moderate |

---

## Recommended Entity Relationships (Priority Order)

### 🥇 TIER 1: CRITICAL RELATIONSHIPS (Must Have)

#### 1. **Company Ownership Hierarchy**
**Relationship**: `(:Company)-[:OWNS]->(:Company)` and `(:Company)-[:SUBSIDIARY_OF]->(:Company)`

**Why Critical:**
- Found in **304+ files** (17% of all filings)
- Core corporate structure information
- Enables ownership chain queries
- Essential for understanding corporate relationships

**Examples Found:**
- Abbey National PLC → Alliance & Leicester plc (subsidiary)
- Abbey National PLC → Bradford & Bingley (subsidiary)
- Banco Santander, S.A. → Abbey National PLC (parent)
- Acergy S.A. ↔ Subsea 7 Inc. (merger/combination)
- Agrium Inc. → CF Industries (proposed acquisition)

**Properties to Store:**
- `ownership_type`: "wholly owned", "majority", "minority", "merger", "acquisition"
- `acquisition_date`: Date of acquisition/merger
- `ownership_percentage`: If available
- `integration_status`: "completed", "in progress", "proposed"
- `transaction_value`: If mentioned

---

#### 2. **Person-Company Employment**
**Relationship**: `(:Person)-[:WORKS_AT]->(:Company)`

**Why Critical:**
- Found in **706+ files** (39% of all filings)
- Most frequently mentioned relationship type
- Essential for executive tracking and corporate governance
- Enables queries about leadership changes

**Examples Found:**
- António Horta-Osório → Abbey National PLC (Chief Executive)
- Matthew Young → Abbey National PLC (Communications Director)
- Kristian Siem → Subsea 7 Inc. (Chairman)
- Multiple directors, officers, executives across all companies

**Properties to Store:**
- `title`: Job title/role
- `role_type`: "CEO", "Director", "Officer", "Signatory", "Contact"
- `start_date`: When they started (if available)
- `end_date`: When they left (if available)
- `phone`: Contact information
- `email`: If available
- `signing_date`: For signatories

---

#### 3. **Company Events**
**Relationship**: `(:Company)-[:HAS_EVENT]->(:Event)`

**Why Critical:**
- Found in **~500+ files** (28%+ of all filings)
- Captures all major corporate actions
- Enables temporal queries and event tracking
- Links companies to their activities

**Event Types Found:**
- **Financial Results**: Quarterly/Annual earnings, profit announcements
- **Mergers & Acquisitions**: Corporate combinations, acquisitions
- **Corporate Restructuring**: Legal structure changes, reorganizations
- **Contract Awards**: Major contract announcements
- **Regulatory Filings**: SEC submissions, compliance events

**Properties to Store:**
- `event_type`: "Financial Results", "Merger", "Acquisition", "Restructuring", "Contract", "Filing"
- `event_date`: When the event occurred
- `title`: Event title/headline
- `description`: Event description
- `filing_id`: Associated SEC filing accession number
- `period`: For financial events (e.g., "Q1 2009")
- `metrics`: Key financial metrics (profit, revenue, etc.)

---

### 🥈 TIER 2: HIGH VALUE RELATIONSHIPS (Should Have)

#### 4. **Company Sector Classification**
**Relationship**: `(:Company)-[:BELONGS_TO_SECTOR]->(:Sector)`

**Why Valuable:**
- Found in **100% of filings** (every filing has SIC code)
- Enables industry-based queries
- Sector analysis and peer comparisons
- Standardized classification

**Properties to Store:**
- `sic_code`: Standard Industrial Classification code
- `sic_description`: Industry description
- `primary_sector`: Boolean flag

---

#### 5. **Company Ratings**
**Relationship**: `(:Company)-[:RATED_BY]->(:Rating)`

**Why Valuable:**
- Found in **~100+ files** (5-10% of filings)
- Credit ratings, analyst ratings
- Important for financial analysis
- Risk assessment

**Properties to Store:**
- `rating_type`: "Credit Rating", "Analyst Rating", "Bond Rating"
- `rating_value`: The actual rating (e.g., "AAA", "BBB+")
- `rating_agency`: Who issued the rating
- `rating_date`: When rated
- `outlook`: "Positive", "Negative", "Stable"

---

### 🥉 TIER 3: NICE TO HAVE RELATIONSHIPS (Optional)

#### 6. **Debentures/Bonds**
**Relationship**: `(:Company)-[:ISSUED]->(:Debenture)`

**Why Optional:**
- Found in **~20-30 files** (1-2% of filings)
- Less common but valuable for debt analysis
- Can be added later if needed

**Properties to Store:**
- `issue_date`: When issued
- `maturity_date`: When it matures
- `principal_amount`: Face value
- `interest_rate`: Coupon rate
- `currency`: Denomination currency

---

## Recommended Graph Schema (Final)

### Node Types

```cypher
(:Company) {
  id: string (CIK),
  name: string,
  cik: string,
  sic_code: string,
  sic_description: string,
  fiscal_year_end: string,
  address_street1: string,
  address_city: string,
  address_state: string,
  address_zip: string,
  address_country: string,
  phone: string,
  sec_file_number: string,
  website: string (optional)
}

(:Person) {
  id: string (name + company),
  name: string,
  title: string,
  role_type: string,
  phone: string (optional),
  email: string (optional)
}

(:Event) {
  id: string (filing_id + event_type),
  event_type: string,
  title: string,
  event_date: date,
  description: string,
  filing_id: string,
  period: string (optional),
  metrics: map (optional)
}

(:Sector) {
  id: string (sic_code),
  sic_code: string,
  name: string,
  description: string
}

(:Rating) {
  id: string (company + agency + date),
  rating_type: string,
  rating_value: string,
  rating_agency: string,
  rating_date: date,
  outlook: string
}

(:Debenture) {
  id: string (company + issue_date),
  issue_date: date,
  maturity_date: date,
  principal_amount: float,
  interest_rate: float,
  currency: string
}
```

### Relationship Types

```cypher
// Tier 1 - Critical
(:Company)-[:OWNS {
  ownership_type: string,
  acquisition_date: date,
  ownership_percentage: float (optional),
  integration_status: string,
  transaction_value: float (optional)
}]->(:Company)

(:Company)-[:SUBSIDIARY_OF {
  acquisition_date: date,
  integration_status: string
}]->(:Company)

(:Person)-[:WORKS_AT {
  title: string,
  role_type: string,
  start_date: date (optional),
  end_date: date (optional),
  phone: string (optional),
  signing_date: date (optional)
}]->(:Company)

(:Company)-[:HAS_EVENT {
  event_date: date,
  filing_id: string
}]->(:Event)

// Tier 2 - High Value
(:Company)-[:BELONGS_TO_SECTOR {
  sic_code: string
}]->(:Sector)

(:Company)-[:RATED_BY {
  rating_date: date,
  outlook: string
}]->(:Rating)

// Tier 3 - Optional
(:Company)-[:ISSUED {
  issue_date: date,
  principal_amount: float
}]->(:Debenture)
```

---

## Relationship Patterns by Filing Type

### 1. **Merger/Acquisition Filings**
**Key Relationships:**
- `(:Company)-[:OWNS]->(:Company)` - Acquisition
- `(:Company)-[:SUBSIDIARY_OF]->(:Company)` - Subsidiary relationship
- `(:Company)-[:HAS_EVENT]->(:Event)` - Merger/Acquisition event
- `(:Person)-[:WORKS_AT]->(:Company)` - Board members, executives involved

**Example**: Acergy S.A. + Subsea 7 Inc. merger (2010)

---

### 2. **Financial Results Filings**
**Key Relationships:**
- `(:Company)-[:HAS_EVENT]->(:Event)` - Quarterly/Annual results
- `(:Person)-[:WORKS_AT]->(:Company)` - CEO, CFO, executives commenting
- `(:Company)-[:BELONGS_TO_SECTOR]->(:Sector)` - Industry context

**Example**: Abbey National PLC Q1 2009 results

---

### 3. **Corporate Restructuring Filings**
**Key Relationships:**
- `(:Company)-[:OWNS]->(:Company)` - Ownership changes
- `(:Company)-[:SUBSIDIARY_OF]->(:Company)` - New subsidiary relationships
- `(:Company)-[:HAS_EVENT]->(:Event)` - Restructuring event
- `(:Person)-[:WORKS_AT]->(:Company)` - Signatories, executives

**Example**: Abbey National PLC + Alliance & Leicester legal structure change

---

### 4. **Rating Announcement Filings**
**Key Relationships:**
- `(:Company)-[:RATED_BY]->(:Rating)` - Credit/analyst ratings
- `(:Company)-[:HAS_EVENT]->(:Event)` - Rating announcement event

---

## Query Patterns Enabled

### 1. **Ownership Chain Queries**
```cypher
// Find all subsidiaries of a company
MATCH (parent:Company {name: "Banco Santander, S.A."})-[:OWNS*]->(sub:Company)
RETURN sub

// Find parent company chain
MATCH (company:Company {name: "Alliance & Leicester plc"})<-[:SUBSIDIARY_OF*]-(parent:Company)
RETURN parent
```

### 2. **Executive Tracking**
```cypher
// Find all executives at a company
MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "ABBEY NATIONAL PLC"})
RETURN p.name, p.title, p.role_type

// Find all companies where a person worked
MATCH (p:Person {name: "António Horta-Osório"})-[:WORKS_AT]->(c:Company)
RETURN c.name, p.title
```

### 3. **Event Timeline**
```cypher
// Find all events for a company in a time period
MATCH (c:Company {name: "ABBEY NATIONAL PLC"})-[:HAS_EVENT]->(e:Event)
WHERE e.event_date >= date('2009-01-01') AND e.event_date <= date('2009-12-31')
RETURN e ORDER BY e.event_date
```

### 4. **Sector Analysis**
```cypher
// Find all companies in a sector
MATCH (c:Company)-[:BELONGS_TO_SECTOR]->(s:Sector {sic_code: "6029"})
RETURN c.name, c.cik
```

### 5. **Merger/Acquisition Analysis**
```cypher
// Find all acquisitions by a company
MATCH (acquirer:Company {name: "AGRIUM INC"})-[:OWNS {ownership_type: "acquisition"}]->(target:Company)
RETURN target.name, acquirer.acquisition_date
```

---

## Implementation Priority

### Phase 1: Core Relationships (Week 1-2)
1. ✅ `(:Company)-[:OWNS]->(:Company)`
2. ✅ `(:Company)-[:SUBSIDIARY_OF]->(:Company)`
3. ✅ `(:Person)-[:WORKS_AT]->(:Company)`
4. ✅ `(:Company)-[:HAS_EVENT]->(:Event)`

### Phase 2: Classification (Week 2-3)
5. ✅ `(:Company)-[:BELONGS_TO_SECTOR]->(:Sector)`

### Phase 3: Financial (Week 3-4)
6. ✅ `(:Company)-[:RATED_BY]->(:Rating)`
7. ⚠️ `(:Company)-[:ISSUED]->(:Debenture)` (if needed)

---

## Data Quality Considerations

### Challenges Identified:
1. **Name Variations**: Companies mentioned with different names (e.g., "A&L" vs "Alliance & Leicester plc")
   - **Solution**: Store name variations in Company node, use fuzzy matching

2. **Date Precision**: Some events have exact dates, others have periods (e.g., "Q1 2009")
   - **Solution**: Store both `event_date` (exact) and `period` (string)

3. **Incomplete Data**: Not all filings have all relationship types
   - **Solution**: Make relationships optional, build incrementally

4. **Historical Data**: Relationships change over time (e.g., acquisitions)
   - **Solution**: Store `start_date` and `end_date` on relationships, or use event-based approach

---

## Recommendations

### ✅ **DO Implement:**
1. **Company ownership hierarchy** - Most valuable for corporate structure
2. **Person-Company employment** - Most frequently mentioned
3. **Company events** - Captures all major activities
4. **Sector classification** - Available in every filing

### ⚠️ **Consider Implementing:**
1. **Ratings** - If financial analysis is important
2. **Debentures** - If debt analysis is needed

### ❌ **Skip for Now:**
1. Complex multi-hop relationships (can be derived from basic relationships)
2. Detailed financial metrics (store in Event properties, not separate nodes)
3. Document-level relationships (files are stored on disk, not in graph)

---

## Next Steps

1. **Update Neo4j Schema** - Implement the recommended node and relationship types
2. **Create Entity Extractor** - Build `graph_builder.py` to extract these relationships
3. **Test on Sample** - Process 10-20 filings to validate the schema
4. **Scale Up** - Process all 1,814 filings once schema is validated

---

## Conclusion

The analysis reveals **4 critical relationship types** that should be prioritized:
1. Company ownership (OWNS, SUBSIDIARY_OF)
2. Person employment (WORKS_AT)
3. Company events (HAS_EVENT)
4. Sector classification (BELONGS_TO_SECTOR)

These relationships appear in **30-40% of all filings** and provide the foundation for powerful graph queries about corporate structures, executive movements, and corporate events.

