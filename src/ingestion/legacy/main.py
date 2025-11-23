#!/usr/bin/env python3
"""
Main entry point for SEC EDGAR filing ingestion.

Usage:
    python -m src.ingestion.main
    python src/ingestion/main.py [start_year] [end_year] [--skip-existing] [--download-dir DIR]
    
Examples:
    # Download 2009-2010 filings
    python src/ingestion/main.py 2009 2010
    
    # Download 2020 filings, re-download existing
    python src/ingestion/main.py 2020 2020 --no-skip-existing
    
    # Download to custom directory
    python src/ingestion/main.py 2009 2010 --download-dir ./my_filings
"""

import sys
import argparse
from .filing_downloader import download_6k_filings


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Download SEC EDGAR 6-K filings for Foreign Private Issuers",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "start_year",
        type=int,
        nargs="?",
        default=2009,
        help="Starting year (inclusive, default: 2009)"
    )
    parser.add_argument(
        "end_year",
        type=int,
        nargs="?",
        default=2010,
        help="Ending year (inclusive, default: 2010)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-download filings even if they already exist"
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default=None,
        help="Custom download directory (default: data/edgar_filings)"
    )
    
    args = parser.parse_args()
    
    if args.start_year > args.end_year:
        print("❌ Error: start_year must be <= end_year")
        sys.exit(1)
    
    if args.start_year < 1994:
        print("⚠️  Warning: SEC EDGAR data may not be available before 1994")
    
    download_6k_filings(
        start_year=args.start_year,
        end_year=args.end_year,
        skip_existing=not args.no_skip_existing,
        download_dir=args.download_dir
    )


if __name__ == "__main__":
    main()

