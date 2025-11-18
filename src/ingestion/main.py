#!/usr/bin/env python3
"""
Main entry point for SEC EDGAR filing ingestion.

Usage:
    python -m src.ingestion.main
    python src/ingestion/main.py
"""

from .filing_downloader import download_6k_filings

if __name__ == "__main__":
    download_6k_filings()

