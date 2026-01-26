-- Performance optimization indexes
-- Run this migration after 001_init.sql for better query performance

-- Partial index for non-completed filings (faster status updates)
-- Only indexes rows where status != 'COMPLETED', reducing index size
CREATE INDEX IF NOT EXISTS idx_filings_id_not_completed 
ON filings(id) 
WHERE status != 'COMPLETED';

-- Covering index for chunk retrieval with content
-- Includes content in the index to avoid heap lookups
CREATE INDEX IF NOT EXISTS idx_filing_chunks_filing_id_covering 
ON filing_chunks(filing_id, chunk_index) 
INCLUDE (content);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_filings_status_date 
ON filings(status, filing_date DESC);

-- Index for CIK lookups with date filtering
CREATE INDEX IF NOT EXISTS idx_filings_cik_date 
ON filings(cik, filing_date DESC);

-- Analyze tables to update query planner statistics
ANALYZE filings;
ANALYZE filing_chunks;
