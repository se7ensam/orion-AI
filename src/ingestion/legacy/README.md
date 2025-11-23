# Legacy Python Downloader

This folder contains the original Python implementation of the SEC EDGAR downloader.

## Status

**DEPRECATED** - This implementation has been replaced by the Node.js version for better I/O performance.

The Node.js implementation is located at: `src/ingestion/nodejs/downloader.js`

## Why Node.js?

- **Better I/O Performance**: Node.js's event-driven, non-blocking I/O model is ideal for network operations
- **Concurrent Downloads**: Better handling of multiple parallel connections
- **Async/Await**: Cleaner async code for I/O-bound operations
- **Native Streams**: Efficient file streaming and processing

## Migration

The Node.js version maintains the same functionality:
- Same rate limiting (10 requests/second)
- Same data structure and file organization
- Same metadata CSV format
- Compatible with existing downloaded files

## Files

- `filing_downloader.py` - Main downloader logic
- `sec_companies.py` - Company index parser
- `main.py` - CLI entry point

## Note

This code is kept for reference and may be removed in future versions.

