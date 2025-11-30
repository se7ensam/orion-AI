"""
Data Loader for EDGAR Filings

Loads and parses EDGAR 6-K filings from disk.
Provides unified interface for accessing filing data.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def get_filings_dir() -> Path:
    """Get the directory where filings are stored."""
    data_dir = os.getenv("ORION_DATA_DIR", "./data")
    return Path(data_dir) / "filings"


def list_filings(year: Optional[int] = None) -> List[Path]:
    """
    List all filing files.
    
    Args:
        year: Optional year filter (e.g., 2009)
        
    Returns:
        List of Path objects to filing .txt files
    """
    filings_dir = get_filings_dir()
    filings = []
    
    if not filings_dir.exists():
        return filings
    
    if year:
        year_dir = filings_dir / str(year)
        if year_dir.exists():
            for file in year_dir.glob("*.txt"):
                if not file.name.startswith("EX-99") and "_" not in file.name:
                    filings.append(file)
    else:
        for year_dir in sorted(filings_dir.iterdir()):
            if year_dir.is_dir() and year_dir.name.isdigit():
                for file in year_dir.glob("*.txt"):
                    if not file.name.startswith("EX-99") and "_" not in file.name:
                        filings.append(file)
    
    return sorted(filings)


def parse_filing_header(txt_path: Path) -> Dict[str, str]:
    """
    Parse the SEC header from a filing text file.
    
    Returns:
        Dictionary with company information from SEC header
    """
    header_data = {}
    
    try:
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(10000)  # Read first 10k chars (header is at the top)
            
            # Extract company name
            name_match = re.search(r'COMPANY CONFORMED NAME:\s+(.+)', content)
            if name_match:
                header_data['company_name'] = name_match.group(1).strip()
            
            # Extract CIK
            cik_match = re.search(r'CENTRAL INDEX KEY:\s+(\d+)', content)
            if cik_match:
                header_data['cik'] = cik_match.group(1).strip()
            
            # Extract SIC code
            sic_match = re.search(r'STANDARD INDUSTRIAL CLASSIFICATION:\s+(.+?)\s*\[(\d+)\]', content)
            if sic_match:
                header_data['sic_description'] = sic_match.group(1).strip()
                header_data['sic_code'] = sic_match.group(2).strip()
            
            # Extract accession number
            acc_match = re.search(r'ACCESSION NUMBER:\s+(.+)', content)
            if acc_match:
                header_data['accession_number'] = acc_match.group(1).strip()
            
            # Extract filing date
            date_match = re.search(r'FILED AS OF DATE:\s+(\d{8})', content)
            if date_match:
                date_str = date_match.group(1)
                try:
                    header_data['filing_date'] = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                except:
                    header_data['filing_date'] = date_str
            
            # Extract form type
            form_match = re.search(r'FORM TYPE:\s+(.+)', content)
            if form_match:
                header_data['form_type'] = form_match.group(1).strip()
            
            # Extract address information
            street1_match = re.search(r'STREET 1:\s+(.+)', content)
            if street1_match:
                header_data['address_street1'] = street1_match.group(1).strip()
            
            city_match = re.search(r'CITY:\s+(.+)', content)
            if city_match:
                header_data['address_city'] = city_match.group(1).strip()
            
            state_match = re.search(r'STATE:\s+(.+)', content)
            if state_match:
                header_data['address_state'] = state_match.group(1).strip()
            
            zip_match = re.search(r'ZIP:\s+(.+)', content)
            if zip_match:
                header_data['address_zip'] = zip_match.group(1).strip()
            
            # Extract phone
            phone_match = re.search(r'BUSINESS PHONE:\s+(.+)', content)
            if phone_match:
                header_data['phone'] = phone_match.group(1).strip()
            
            # Extract SEC file number
            sec_file_match = re.search(r'SEC FILE NUMBER:\s+(.+)', content)
            if sec_file_match:
                header_data['sec_file_number'] = sec_file_match.group(1).strip()
            
            # Extract fiscal year end
            fiscal_match = re.search(r'FISCAL YEAR END:\s+(\d{4})', content)
            if fiscal_match:
                header_data['fiscal_year_end'] = fiscal_match.group(1).strip()
            
    except Exception as e:
        print(f"Error parsing header from {txt_path}: {e}")
    
    return header_data


def parse_filing_content(txt_path: Path) -> Dict:
    """
    Parse the full content of a filing.
    
    Returns:
        Dictionary with parsed content including HTML text
    """
    content_data = {
        'raw_text': '',
        'html_content': '',
        'year': None
    }
    
    try:
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            content_data['raw_text'] = content
            
            # Extract year from file path or content
            year_match = re.search(r'CONFORMED PERIOD OF REPORT:\s+(\d{4})', content)
            if year_match:
                content_data['year'] = int(year_match.group(1)[:4])
            else:
                # Try to get from directory name
                parent_dir = txt_path.parent.name
                if parent_dir.isdigit():
                    content_data['year'] = int(parent_dir)
            
            # Extract HTML content from <TEXT> tags
            text_matches = re.findall(r'<TEXT>(.*?)</TEXT>', content, re.DOTALL)
            if text_matches:
                content_data['html_content'] = text_matches[0]
            
    except Exception as e:
        print(f"Error parsing content from {txt_path}: {e}")
    
    return content_data


def get_filing_data(txt_path: Path) -> Dict:
    """
    Get complete filing data (header + content).
    
    Returns:
        Dictionary with all filing information
    """
    header = parse_filing_header(txt_path)
    content = parse_filing_content(txt_path)
    
    # Combine header and content
    filing_data = {**header, **content}
    filing_data['file_path'] = str(txt_path)
    filing_data['file_name'] = txt_path.name
    
    return filing_data


def get_filings_by_company(company_name: str, year: Optional[int] = None) -> List[Dict]:
    """
    Get all filings for a specific company.
    
    Args:
        company_name: Company name to search for
        year: Optional year filter
        
    Returns:
        List of filing data dictionaries
    """
    all_filings = list_filings(year)
    company_filings = []
    
    for filing_path in all_filings:
        header = parse_filing_header(filing_path)
        if header.get('company_name', '').upper() == company_name.upper():
            filing_data = get_filing_data(filing_path)
            company_filings.append(filing_data)
    
    return company_filings


def get_filings_by_year(year: int) -> List[Dict]:
    """
    Get all filings for a specific year.
    
    Args:
        year: Year to filter by
        
    Returns:
        List of filing data dictionaries
    """
    filings = list_filings(year)
    return [get_filing_data(f) for f in filings]


if __name__ == "__main__":
    # Test the data loader
    print("Testing EDGAR Filing Data Loader")
    print("=" * 50)
    
    # List some filings
    filings = list_filings(2009)
    print(f"\nFound {len(filings)} filings for 2009")
    
    if filings:
        # Test parsing first filing
        test_filing = filings[0]
        print(f"\nTesting parsing: {test_filing.name}")
        data = get_filing_data(test_filing)
        
        print(f"\nCompany: {data.get('company_name', 'N/A')}")
        print(f"CIK: {data.get('cik', 'N/A')}")
        print(f"SIC Code: {data.get('sic_code', 'N/A')}")
        print(f"Filing Date: {data.get('filing_date', 'N/A')}")
        print(f"Accession: {data.get('accession_number', 'N/A')}")

