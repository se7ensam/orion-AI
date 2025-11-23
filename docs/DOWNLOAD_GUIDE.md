# SEC EDGAR Download Guide

## Quick Start

### Prerequisites

Make sure you have activated the conda environment:
```bash
conda activate orion
```

### Basic Usage

Download 6-K filings for a date range:
```bash
python -m src.cli download --start-year 2009 --end-year 2010
```

### Command-Line Options

```bash
# Download specific years
python -m src.cli download --start-year 2020 --end-year 2021

# Re-download existing filings (don't skip)
python -m src.cli download --start-year 2009 --end-year 2010 --no-skip-existing

# Download to custom directory
python -m src.cli download --start-year 2009 --end-year 2010 --download-dir ./my_filings

# Show help
python -m src.cli download --help
```

## What Gets Downloaded

1. **Company Index Files** → `metadata/` folder
   - SEC company index files for each quarter
   - Used to identify companies with 6-K filings

2. **FPI List** → `fpi_list.csv`
   - List of all Foreign Private Issuers (FPIs) that filed 6-K forms
   - Contains: company_name, cik

3. **Filing Files** → `Edgar_filings/` folder
   - HTML filing index pages
   - Complete submission text files (.txt)
   - EX-99 exhibits (extracted from filings)

4. **Metadata** → `fpi_6k_metadata.csv`
   - CSV with all downloaded filing metadata
   - Columns: Company Name, CIK, Date, Accession Number, HTML File, TXT File, Exhibits

## File Structure

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

## Features

✅ **Resume Capability**: Automatically skips already downloaded filings  
✅ **Rate Limiting**: Respects SEC rate limits (0.2s delay between requests)  
✅ **Error Handling**: Handles timeouts, rate limits, and network errors  
✅ **Progress Tracking**: Shows progress bar during download  
✅ **Exhibit Extraction**: Automatically extracts all EX-99 exhibits  

## Testing

Test the downloader with a small sample:
```bash
python test_download.py
```

## Notes

- **User-Agent**: Uses `sambitsrcm@gmail.com` as required by SEC
- **Rate Limits**: 0.2 second delay between requests (SEC requirement)
- **Timeouts**: 30s for API calls, 60s for large filing downloads
- **Date Range**: Default is 2009-2010, but can be customized

## Troubleshooting

### Connection Errors
- Check your internet connection
- Verify SEC website is accessible: https://www.sec.gov

### Rate Limiting
- If you see 429 errors, the script will automatically wait and retry
- Consider downloading smaller date ranges if issues persist

### Missing Exhibits
- Some filings may not have EX-99 exhibits
- Check the `fpi_6k_metadata.csv` to see which filings have exhibits

