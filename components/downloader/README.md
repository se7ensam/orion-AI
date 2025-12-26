# Downloader Service

SEC EDGAR 6-K Filing Downloader Service (TypeScript)

## Prerequisites

- Node.js 20.x or higher
- npm

## Setup

### 1. Install Dependencies

```bash
cd components/downloader
npm install
```

### 2. Build TypeScript

```bash
npm run build
```

This compiles TypeScript to JavaScript in the `dist/` directory.

## Running the Downloader

### Method 1: Direct Node.js Execution

After building, run directly:

```bash
# From components/downloader directory
node dist/index.js 2009 2010

# With options
node dist/index.js 2009 2010 --max-workers 20

# Re-download existing files
node dist/index.js 2009 2010 --no-skip-existing

# Custom download directory
node dist/index.js 2009 2010 --download-dir /custom/path
```

### Method 2: Using npm Script

```bash
# From components/downloader directory
npm start 2009 2010

# Note: npm start doesn't pass arguments, so use Method 1 or Method 3
```

### Method 3: Using Helper Script

```bash
./run.sh 2009 2010 --max-workers 20
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `startYear` | Starting year (inclusive) | 2009 |
| `endYear` | Ending year (inclusive) | 2010 |
| `--max-workers N` | Number of parallel workers | 10 |
| `--no-skip-existing` | Re-download existing files | false (skip existing) |
| `--download-dir DIR` | Custom download directory | `data/edgar_filings` |
| `--help, -h` | Show help message | - |

## Examples

```bash
# Download 2009-2010 filings with default settings
node dist/index.js 2009 2010

# Download 2020-2021 with 20 parallel workers
node dist/index.js 2020 2021 --max-workers 20

# Download and re-download existing files
node dist/index.js 2009 2010 --no-skip-existing

# Download to custom directory
node dist/index.js 2009 2010 --download-dir ./my_filings

# Via Python CLI with all options
python -m src.cli download \
  --start-year 2020 \
  --end-year 2021 \
  --max-workers 20 \
  --no-skip-existing
```

## Development

### Watch Mode (Auto-rebuild on changes)

```bash
npm run dev
```

This watches for TypeScript file changes and automatically rebuilds.

### Clean Build

```bash
npm run clean  # Remove dist/
npm run build  # Rebuild
```

## Output

The downloader saves files to:
- **Filings**: `data/edgar_filings/` (or custom directory)
- **Metadata**: `data/fpi_6k_metadata.csv`
- **FPI List**: `data/fpi_list.csv`
- **Index Cache**: `data/metadata/`

## Environment Variables

- `ORION_DATA_DIR`: Base data directory (default: `./data`)

## Troubleshooting

### Service not found error

If you see "Downloader service not found", build the service:

```bash
cd components/downloader
npm install
npm run build
```

### Node.js not found

Install Node.js 20.x or higher:
- macOS: `brew install node`
- Linux: Follow [Node.js installation guide](https://nodejs.org/)
- Windows: Download from [nodejs.org](https://nodejs.org/)

### TypeScript compilation errors

Check TypeScript version:
```bash
npx tsc --version
```

Should be 5.3.0 or higher. Update if needed:
```bash
npm install typescript@latest --save-dev
```

