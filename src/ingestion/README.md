# SEC EDGAR Filing Ingestion

This module handles downloading and processing SEC EDGAR filings, specifically 6-K forms for Foreign Private Issuers (FPIs).

## Structure

```
src/ingestion/
├── __init__.py              # Module exports
├── sec_companies.py         # Company index parser (downloads SEC index files)
├── filing_downloader.py     # Main filing downloader (6-K forms + EX-99 exhibits)
└── main.py                  # Entry point script
```

## Usage

### Basic Usage

```python
from src.ingestion import download_6k_filings

# Download all 6-K filings for 2009-2010
download_6k_filings(start_year=2009, end_year=2010)
```

### Get FPI List Only

```python
from src.ingestion import get_fpi_list

# Get list of companies that filed 6-K forms
companies = get_fpi_list(start_year=2009, end_year=2010)
```

### Command Line

```bash
# Run the main downloader
python -m src.ingestion.main
```

## Features

- ✅ Downloads SEC company index files
- ✅ Parses 6-K filings from index
- ✅ Downloads filing HTML and TXT files
- ✅ Extracts EX-99 exhibits (with collision handling)
- ✅ Respects SEC rate limits (0.2s delay)
- ✅ Saves metadata to CSV
- ✅ Proper error handling

## Output Structure

```
Edgar_filings/
└── {Company Name}/
    └── {Year}_{Company Name}_{CIK}/
        └── {Accession Number}/
            ├── filing.html
            ├── {accession}.txt
            ├── EX-99.1.txt
            ├── EX-99.2.txt
            └── ...
```

## Files Generated

- `fpi_list.csv` - List of all FPIs that filed 6-K forms
- `fpi_6k_metadata.csv` - Metadata for all downloaded filings
- `metadata/` - Cached SEC company index files

## Configuration

Default date range: 2009-2010 (configurable in function calls)

Rate limiting: 0.2 seconds between requests (SEC requirement)

