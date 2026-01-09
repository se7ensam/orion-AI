CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE filings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cik TEXT NOT NULL,
  accession_number TEXT NOT NULL,
  filing_date DATE NOT NULL,
  form_type TEXT NOT NULL,
  source_url TEXT NOT NULL,
  local_path TEXT,
  raw_text TEXT,
  status TEXT CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')) DEFAULT 'QUEUED',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(cik, accession_number)
);

CREATE TABLE filing_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  filing_id UUID REFERENCES filings(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_filing_chunks_filing_id ON filing_chunks(filing_id);
CREATE INDEX IF NOT EXISTS idx_filing_chunks_filing_id_index ON filing_chunks(filing_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
CREATE INDEX IF NOT EXISTS idx_filings_status ON filings(status);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);
