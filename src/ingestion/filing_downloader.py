"""
SEC EDGAR 6-K Filing Downloader

Downloads 6-K filings from SEC EDGAR and extracts EX-99 exhibits.
"""

import os
import csv
import time
import requests
import re
from datetime import datetime
from typing import Optional, Tuple, List
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import here to avoid circular dependency - get_fpi_list is called in download_6k_filings
from .sec_companies import get_fpi_list

HEADERS = {"User-Agent": "sambitsrcm@gmail.com"}
SUBMISSION_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"

# Default date range
START_DATE = datetime(2009, 1, 1)
END_DATE = datetime(2010, 12, 31)

DOWNLOAD_ROOT = "./Edgar_filings"


def format_cik(cik: str) -> str:
    """Format CIK to 10-digit zero-padded string."""
    return cik.zfill(10)


def get_submission_json(cik: str) -> Optional[dict]:
    """
    Fetch submission JSON for a company from SEC API.
    
    Args:
        cik: Company CIK identifier
        
    Returns:
        Submission JSON data or None if fetch fails
    """
    url = SUBMISSION_URL.format(cik=format_cik(cik))
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching {cik}: {e}")
        return None


def extract_exhibits_all(file_path: str, folder: str) -> List[str]:
    """
    Extract all EX-99 exhibits from a filing text file.
    
    Args:
        file_path: Path to the filing text file
        folder: Folder where exhibits should be saved
        
    Returns:
        List of paths to saved exhibit files
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    exhibits_saved = []
    exhibit_counter = {}  # Track multiple exhibits of same type

    # Split into <DOCUMENT> blocks
    docs = re.split(r"<DOCUMENT>", text)
    for doc in docs:
        type_match = re.search(r"<TYPE>(.+)", doc)
        
        if type_match:
            doctype = type_match.group(1).strip().upper()
            
            # Extract ALL EX-99 exhibits
            if doctype.startswith("EX-99"):
                match = re.search(r"<TEXT>(.*)</TEXT>", doc, re.DOTALL | re.IGNORECASE)
                if match:
                    raw_html = match.group(1)
                    soup = BeautifulSoup(raw_html, "html.parser")
                    clean_text = soup.get_text(separator="\n").strip()
                    
                    # Handle multiple exhibits of same type (e.g., EX-99.1, EX-99.1 again)
                    if doctype in exhibit_counter:
                        exhibit_counter[doctype] += 1
                        exhibit_filename = f"{doctype}_{exhibit_counter[doctype]}.txt"
                    else:
                        exhibit_counter[doctype] = 0
                        exhibit_filename = f"{doctype}.txt"
                    
                    # Save exhibit to file
                    exhibit_file = os.path.join(folder, exhibit_filename)
                    with open(exhibit_file, "w", encoding="utf-8") as f:
                        f.write(clean_text)
                    
                    exhibits_saved.append(exhibit_file)

    return exhibits_saved


def download_filing(company_name: str, cik: str, accession: str, filing_date: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Download a single 6-K filing and extract exhibits.
    
    Args:
        company_name: Company name
        cik: Company CIK
        accession: Accession number
        filing_date: Filing date string (YYYY-MM-DD)
        
    Returns:
        Tuple of (html_path, txt_path, exhibits_list) or (None, None, []) on failure
    """
    acc_nodash = accession.replace("-", "")
    year = filing_date[:4]

    # Folder per filing
    folder = os.path.join(
        DOWNLOAD_ROOT,
        company_name,
        f"{year}_{company_name}_{cik}",
        accession
    )
    os.makedirs(folder, exist_ok=True)

    # File paths
    html_path = os.path.join(folder, "filing.html")
    txt_path = os.path.join(folder, f"{accession}.txt")

    filing_url = f"{ARCHIVE_BASE}/{int(cik)}/{acc_nodash}/{accession}-index.html"

    exhibits = []

    try:
        # Download index HTML
        r = requests.get(filing_url, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Fix relative URLs
        for tag in soup.find_all(["link", "script", "img", "a"]):
            attr = "href" if tag.name in ["link", "a"] else "src"
            if tag.has_attr(attr) and tag[attr].startswith("/"):
                tag[attr] = urljoin("https://www.sec.gov", tag[attr])

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        # Find Complete submission text file link
        txt_link = None
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3 and "Complete submission text file" in cols[1].get_text(strip=True):
                link = cols[2].find("a")
                if link and link.get("href"):
                    txt_link = urljoin("https://www.sec.gov", link["href"])
                    break

        if txt_link:
            txt_resp = requests.get(txt_link, headers=HEADERS)
            txt_resp.raise_for_status()
            with open(txt_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(txt_resp.text)

            # Extract Exhibits
            exhibits = extract_exhibits_all(txt_path, folder)
        
        return html_path, txt_path, exhibits

    except Exception as e:
        print(f"❌ Failed to download {accession}: {e}")
        return None, None, []


def log_metadata_row(metadata: dict, file: str = "fpi_6k_metadata.csv"):
    """
    Append a metadata row to CSV file.
    
    Args:
        metadata: Dictionary with metadata fields
        file: CSV file path
    """
    exists = os.path.exists(file)
    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metadata.keys())
        if not exists:
            writer.writeheader()
        writer.writerow(metadata)


def process_fpi_entry(entry: dict, start_date: datetime = START_DATE, end_date: datetime = END_DATE):
    """
    Process a single FPI entry: fetch filings and download 6-K forms.
    
    Args:
        entry: Dictionary with 'cik' and 'company_name'
        start_date: Start date for filing filter
        end_date: End date for filing filter
    """
    cik = entry["cik"]
    company = entry["company_name"]

    data = get_submission_json(cik)
    if not data:
        return

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])

    for form, date_str, accession in zip(forms, dates, accessions):
        if form != "6-K":
            continue
        try:
            filing_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if not (start_date <= filing_date <= end_date):
            continue

        html_path, txt_path, exhibits = download_filing(company, cik, accession, date_str)
        if html_path:
            log_metadata_row({
                "Company Name": company.replace("_", " "),
                "CIK": cik,
                "Date": date_str,
                "Accession Number": accession,
                "HTML File": html_path,
                "TXT File": txt_path if txt_path else "",
                "Exhibits": ";".join(exhibits) if exhibits else ""
            })
        time.sleep(0.2)  # SEC rate limit


def download_6k_filings(start_year: int = 2009, end_year: int = 2010):
    """
    Main function to download all 6-K filings for FPIs in date range.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    fpis = get_fpi_list(start_year, end_year)
    for fpi in tqdm(fpis, desc="Downloading 6-K filings"):
        process_fpi_entry(fpi, start_date, end_date)

    print("✅ All 6-K filings downloaded.")


if __name__ == "__main__":
    download_6k_filings()

