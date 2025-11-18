"""
SEC EDGAR Filing Ingestion Module

This module handles downloading and processing SEC EDGAR filings,
specifically 6-K forms for Foreign Private Issuers (FPIs).
"""

from .sec_companies import get_fpi_list
from .filing_downloader import download_6k_filings

__all__ = ['get_fpi_list', 'download_6k_filings']

