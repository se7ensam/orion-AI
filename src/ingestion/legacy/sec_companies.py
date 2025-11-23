"""
SEC Company Index Parser

Downloads and parses SEC company index files to identify companies
that have filed 6-K forms (Foreign Private Issuers).
"""

import os
import requests
import csv
from typing import List, Dict

HEADERS = {"User-Agent": "sambitsrcm@gmail.com"}
SEC_FTP_BASE = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/company.idx"


def get_data_dir() -> str:
    """
    Get the data directory from environment variable or use default.
    
    Returns:
        Path to data directory (default: ./data)
    """
    return os.getenv("ORION_DATA_DIR", "./data")


def get_metadata_dir() -> str:
    """
    Get the metadata directory for SEC company index files.
    
    Returns:
        Path to metadata directory
    """
    return os.path.join(get_data_dir(), "metadata")


def get_fpi_list_path() -> str:
    """
    Get the path to fpi_list.csv file.
    
    Returns:
        Path to fpi_list.csv
    """
    return os.path.join(get_data_dir(), "fpi_list.csv")


def download_company_idx(year: int, qtr: int) -> str:
    """
    Download SEC company index file for a specific year and quarter.
    
    Args:
        year: Year (e.g., 2009)
        qtr: Quarter (1-4)
        
    Returns:
        Index file content as string, or None if download fails
    """
    url = SEC_FTP_BASE.format(year=year, qtr=qtr)
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        # Create metadata folder if it doesn't exist
        metadata_dir = get_metadata_dir()
        os.makedirs(metadata_dir, exist_ok=True)
        
        # Save file locally
        file_path = os.path.join(metadata_dir, f"{year}_Q{qtr}_company.idx")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        return response.text
    except Exception as e:
        print(f"❌ Could not download index for {year} Q{qtr}: {e}")
        return None


def parse_idx_file(idx_text: str) -> Dict[str, Dict[str, str]]:
    """
    Parse SEC company index file to extract companies that filed 6-K forms.
    
    Args:
        idx_text: Content of the company index file
        
    Returns:
        Dictionary mapping CIK to company info (company_name, cik)
    """
    fpi_dict = {}
    lines = idx_text.splitlines()

    # Skip first ~10 lines (header info)
    for line in lines[10:]:
        try:
            form_type = line[62:74].strip()
            if form_type == "6-K":
                company_name = line[0:62].strip()
                cik = line[74:86].strip()
                if cik not in fpi_dict:
                    fpi_dict[cik] = {"company_name": company_name, "cik": cik}
        except IndexError:
            continue

    return fpi_dict


def collect_fpis(years: List[int]) -> List[Dict[str, str]]:
    """
    Collect all companies that filed 6-K forms across specified years.
    
    Args:
        years: List of years to process (e.g., [2009, 2010])
        
    Returns:
        List of company dictionaries with company_name and cik
    """
    all_fpis = {}
    for year in years:
        for qtr in range(1, 5):
            print(f"Checking {year} Q{qtr}...")
            idx_text = download_company_idx(year, qtr)
            if idx_text:
                fpis = parse_idx_file(idx_text)
                all_fpis.update(fpis)
    return list(all_fpis.values())


def get_fpi_list(start_year: int = 2009, end_year: int = 2010) -> List[Dict[str, str]]:
    """
    Get list of Foreign Private Issuers (FPIs) that filed 6-K forms.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
        
    Returns:
        List of company dictionaries with company_name and cik
    """
    years = list(range(start_year, end_year + 1))
    fpi_companies = collect_fpis(years)
    
    # Ensure data directory exists
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    
    # Save to CSV
    fpi_list_path = get_fpi_list_path()
    with open(fpi_list_path, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company_name", "cik"])
        writer.writeheader()
        writer.writerows(fpi_companies)
    
    print(f"✅ Saved {len(fpi_companies)} FPIs to {fpi_list_path}")
    return fpi_companies


# Optional: for standalone run
if __name__ == "__main__":
    get_fpi_list()

