"""
SEC EDGAR Filing Ingestion Module

This module handles downloading and processing SEC EDGAR filings,
specifically 6-K forms for Foreign Private Issuers (FPIs).

Note: The download functionality has been moved to Node.js for better I/O performance.
See src/ingestion/nodejs/downloader.js

Legacy Python code is available in src/ingestion/legacy/
"""

# Legacy imports kept for backward compatibility
try:
    from .legacy.sec_companies import get_fpi_list
    from .legacy.filing_downloader import download_6k_filings
    __all__ = ['get_fpi_list', 'download_6k_filings']
except ImportError:
    # If legacy code is not available, provide stubs
    def get_fpi_list(*args, **kwargs):
        raise NotImplementedError("Python downloader has been moved to Node.js. Use the CLI: python -m src.cli download")
    
    def download_6k_filings(*args, **kwargs):
        raise NotImplementedError("Python downloader has been moved to Node.js. Use the CLI: python -m src.cli download")

__all__ = ['get_fpi_list', 'download_6k_filings']

