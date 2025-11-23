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
from typing import Optional, Tuple, List, Dict, TYPE_CHECKING
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading

if TYPE_CHECKING:
    from tqdm import tqdm as tqdm_type
else:
    tqdm_type = tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import here to avoid circular dependency - get_fpi_list is called in download_6k_filings
from .sec_companies import get_fpi_list

HEADERS = {"User-Agent": "sambitsrcm@gmail.com"}
SUBMISSION_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"

# SEC EDGAR rate limit: 10 requests per second
SEC_RATE_LIMIT = 10  # requests per second
SEC_MIN_DELAY = 1.0 / SEC_RATE_LIMIT  # 0.1 seconds between requests

# Default date range
START_DATE = datetime(2009, 1, 1)
END_DATE = datetime(2010, 12, 31)


def get_data_dir() -> str:
    """
    Get the data directory from environment variable or use default.
    
    Returns:
        Path to data directory (default: ./data)
    """
    return os.getenv("ORION_DATA_DIR", "./data")


def get_download_root() -> str:
    """
    Get the download root directory for filings.
    
    Returns:
        Path to edgar_filings directory
    """
    return os.path.join(get_data_dir(), "edgar_filings")


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


def get_metadata_csv_path() -> str:
    """
    Get the path to fpi_6k_metadata.csv file.
    
    Returns:
        Path to fpi_6k_metadata.csv
    """
    return os.path.join(get_data_dir(), "fpi_6k_metadata.csv")


# Global variable for backward compatibility (will be set in download_6k_filings)
DOWNLOAD_ROOT = get_download_root()


class RateLimiter:
    """Thread-safe rate limiter for SEC EDGAR requests."""
    
    def __init__(self, max_rate: float = SEC_RATE_LIMIT):
        """
        Initialize rate limiter.
        
        Args:
            max_rate: Maximum requests per second
        """
        self.max_rate = max_rate
        self.min_interval = 1.0 / max_rate
        self.last_request_time = 0.0
        self.lock = Lock()
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


# Global rate limiter instance
_rate_limiter = None
_rate_limiter_lock = Lock()


def get_rate_limiter(max_rate: float = SEC_RATE_LIMIT) -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    with _rate_limiter_lock:
        if _rate_limiter is None:
            _rate_limiter = RateLimiter(max_rate)
        return _rate_limiter


def format_cik(cik: str) -> str:
    """Format CIK to 10-digit zero-padded string."""
    return cik.zfill(10)


def get_submission_json(cik: str, rate_limiter: Optional[RateLimiter] = None) -> Optional[dict]:
    """
    Fetch submission JSON for a company from SEC API.
    
    Args:
        cik: Company CIK identifier
        rate_limiter: Optional rate limiter instance
        
    Returns:
        Submission JSON data or None if fetch fails
    """
    # Apply rate limiting
    if rate_limiter:
        rate_limiter.wait()
    else:
        time.sleep(SEC_MIN_DELAY)  # Fallback to fixed delay
    
    url = SUBMISSION_URL.format(cik=format_cik(cik))
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout fetching submissions for CIK {cik}")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"⚠️  Rate limited for CIK {cik}, waiting 5 seconds...")
            time.sleep(5)
            return get_submission_json(cik, rate_limiter=rate_limiter)  # Retry once
        print(f"❌ HTTP error fetching {cik}: {e}")
        return None
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


def download_filing(company_name: str, cik: str, accession: str, filing_date: str, skip_existing: bool = True, rate_limiter: Optional[RateLimiter] = None) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Download a single 6-K filing and extract exhibits.
    
    Args:
        company_name: Company name
        cik: Company CIK
        accession: Accession number
        filing_date: Filing date string (YYYY-MM-DD)
        skip_existing: If True, skip if filing already downloaded
        
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
    
    # Check if already downloaded
    if skip_existing and os.path.exists(html_path) and os.path.exists(txt_path):
        # Check if exhibits exist
        exhibits = [f for f in os.listdir(folder) if f.startswith("EX-99") and f.endswith(".txt")]
        exhibit_paths = [os.path.join(folder, ex) for ex in exhibits]
        return html_path, txt_path, exhibit_paths

    filing_url = f"{ARCHIVE_BASE}/{int(cik)}/{acc_nodash}/{accession}-index.html"

    exhibits = []

    try:
        # Apply rate limiting before download
        if rate_limiter:
            rate_limiter.wait()
        else:
            time.sleep(SEC_MIN_DELAY)  # Fallback to fixed delay
        
        # Download index HTML
        r = requests.get(filing_url, headers=HEADERS, timeout=30)
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
            # Apply rate limiting before downloading text file
            if rate_limiter:
                rate_limiter.wait()
            else:
                time.sleep(SEC_MIN_DELAY)  # Fallback to fixed delay
            
            txt_resp = requests.get(txt_link, headers=HEADERS, timeout=60)
            txt_resp.raise_for_status()
            with open(txt_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(txt_resp.text)

            # Extract Exhibits
            exhibits = extract_exhibits_all(txt_path, folder)
        
        return html_path, txt_path, exhibits

    except Exception as e:
        print(f"❌ Failed to download {accession}: {e}")
        return None, None, []


def log_metadata_row(metadata: dict, file: Optional[str] = None):
    """
    Append a metadata row to CSV file.
    
    Args:
        metadata: Dictionary with metadata fields
        file: CSV file path (default: data/fpi_6k_metadata.csv)
    """
    if file is None:
        file = get_metadata_csv_path()
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(file), exist_ok=True)
    
    exists = os.path.exists(file)
    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metadata.keys())
        if not exists:
            writer.writeheader()
        writer.writerow(metadata)


def process_fpi_entry(entry: dict, start_date: datetime = START_DATE, end_date: datetime = END_DATE, skip_existing: bool = True, pbar: Optional[tqdm_type] = None, pbar_lock: Optional[Lock] = None, rate_limiter: Optional[RateLimiter] = None):
    """
    Process a single FPI entry: fetch filings and download 6-K forms.
    
    Args:
        entry: Dictionary with 'cik' and 'company_name'
        start_date: Start date for filing filter
        end_date: End date for filing filter
        skip_existing: If True, skip already downloaded filings
        pbar: Optional progress bar to update
        pbar_lock: Optional lock for thread-safe progress bar updates
        rate_limiter: Optional rate limiter for SEC EDGAR requests
    """
    cik = entry["cik"]
    company = entry["company_name"]

    data = get_submission_json(cik, rate_limiter=rate_limiter)
    if not data:
        return 0

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])

    filings_processed = 0
    filings_skipped = 0
    
    for form, date_str, accession in zip(forms, dates, accessions):
        if form != "6-K":
            continue
        try:
            filing_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if not (start_date <= filing_date <= end_date):
            continue

        # Check if file already exists before downloading
        acc_nodash = accession.replace("-", "")
        year = date_str[:4]
        folder = os.path.join(
            DOWNLOAD_ROOT,
            company,
            f"{year}_{company}_{cik}",
            accession
        )
        html_path_check = os.path.join(folder, "filing.html")
        txt_path_check = os.path.join(folder, f"{accession}.txt")
        
        was_existing = skip_existing and os.path.exists(html_path_check) and os.path.exists(txt_path_check)
        
        html_path, txt_path, exhibits = download_filing(company, cik, accession, date_str, skip_existing=skip_existing, rate_limiter=rate_limiter)
        
        # Update progress bar for each filing processed (downloaded or skipped)
        if pbar:
            if pbar_lock:
                with pbar_lock:
                    pbar.update(1)
            else:
                pbar.update(1)
        
        if html_path:
            # Only log if not already in metadata (check if we should update)
            log_metadata_row({
                "Company Name": company.replace("_", " "),
                "CIK": cik,
                "Date": date_str,
                "Accession Number": accession,
                "HTML File": html_path,
                "TXT File": txt_path if txt_path else "",
                "Exhibits": ";".join(exhibits) if exhibits else ""
            })
            
            if was_existing:
                filings_skipped += 1
            else:
                filings_processed += 1
            
            if pbar:
                status_info = {"company": company[:30], "downloaded": filings_processed}
                if filings_skipped > 0:
                    status_info["skipped"] = filings_skipped
                if pbar_lock:
                    with pbar_lock:
                        pbar.set_postfix(status_info)
                else:
                    pbar.set_postfix(status_info)
        # Rate limiting is now handled by rate_limiter in download_filing
    
    return filings_processed


def count_total_filings(fpis: List[dict], start_date: datetime, end_date: datetime, rate_limiter: Optional[RateLimiter] = None) -> int:
    """
    Count total number of filings to download.
    
    Args:
        fpis: List of FPI entries
        start_date: Start date filter
        end_date: End date filter
        rate_limiter: Optional rate limiter for API calls
        
    Returns:
        Total number of filings
    """
    total = 0
    print("📊 Counting total filings to download...")
    # Use a rate limiter for counting phase too
    if rate_limiter is None:
        rate_limiter = RateLimiter(SEC_RATE_LIMIT)
    for fpi in tqdm(fpis, desc="Scanning", unit=" company", leave=False, 
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'):
        cik = fpi["cik"]
        data = get_submission_json(cik, rate_limiter=rate_limiter)
        if not data:
            continue
        
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        
        for form, date_str in zip(forms, dates):
            if form != "6-K":
                continue
            try:
                filing_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if start_date <= filing_date <= end_date:
                total += 1
        # Rate limiting handled by rate_limiter in get_submission_json
    
    return total


def download_6k_filings(start_year: int = 2009, end_year: int = 2010, skip_existing: bool = True, download_dir: str = None, max_workers: int = 5):
    """
    Main function to download all 6-K filings for FPIs in date range.
    
    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)
        skip_existing: If True, skip already downloaded filings
        download_dir: Custom download directory (default: data/edgar_filings)
        max_workers: Number of parallel threads (default: 5, set to 1 for sequential)
    """
    global DOWNLOAD_ROOT
    
    # Set download root
    if download_dir:
        DOWNLOAD_ROOT = download_dir
    else:
        DOWNLOAD_ROOT = get_download_root()
    
    # Ensure data directories exist
    os.makedirs(DOWNLOAD_ROOT, exist_ok=True)
    os.makedirs(get_metadata_dir(), exist_ok=True)
    os.makedirs(get_data_dir(), exist_ok=True)
    
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    print(f"📥 Starting download of 6-K filings from {start_year} to {end_year}")
    print(f"📁 Data directory: {get_data_dir()}")
    print(f"📁 Download directory: {DOWNLOAD_ROOT}")
    print(f"⏭️  Skip existing: {skip_existing}")
    print("-" * 60)
    
    fpis = get_fpi_list(start_year, end_year)
    print(f"📊 Found {len(fpis)} companies with 6-K filings")
    
    # Initialize rate limiter for counting phase
    counting_limiter = RateLimiter(max_rate=SEC_RATE_LIMIT)
    
    # Count total filings for accurate progress
    total_filings = count_total_filings(fpis, start_date, end_date, counting_limiter)
    print(f"📄 Found {total_filings} total filings to download")
    print("-" * 60)
    
    # Create progress bar for filings with speed display
    pbar = tqdm(total=total_filings, desc="Downloading", unit="file", 
                unit_scale=False,
                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}')
    
    # Thread-safe lock for progress bar updates
    pbar_lock = Lock() if max_workers > 1 else None
    
    total_downloaded = 0
    
    # Initialize main download rate limiter
    main_rate_limiter = RateLimiter(max_rate=SEC_RATE_LIMIT)
    
    if max_workers > 1:
        # Multi-threaded download
        print(f"🚀 Using {max_workers} parallel threads for faster downloads")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_fpi = {
                executor.submit(process_fpi_entry, fpi, start_date, end_date, skip_existing, pbar, pbar_lock, main_rate_limiter): fpi 
                for fpi in fpis
            }
            
            # Process completed tasks
            for future in as_completed(future_to_fpi):
                try:
                    count = future.result()
                    total_downloaded += count
                except Exception as e:
                    fpi = future_to_fpi[future]
                    print(f"❌ Error processing {fpi.get('company_name', 'unknown')}: {e}")
    else:
        # Sequential download (original behavior)
        for fpi in fpis:
            count = process_fpi_entry(fpi, start_date, end_date, skip_existing=skip_existing, pbar=pbar, pbar_lock=pbar_lock, rate_limiter=main_rate_limiter)
            total_downloaded += count
    
    pbar.close()
    
    print("\n✅ All 6-K filings downloaded.")
    print(f"📊 Downloaded {total_downloaded} filings from {len(fpis)} companies")
    print(f"📁 Files saved to: {DOWNLOAD_ROOT}")
    print(f"📋 Metadata saved to: {get_metadata_csv_path()}")


if __name__ == "__main__":
    download_6k_filings()

