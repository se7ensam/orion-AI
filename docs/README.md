# Orion Documentation

Welcome to the Orion documentation. This directory contains all project documentation.

## 📚 Documentation Index

### Getting Started
- **[Installation Guide](INSTALLATION.md)** - Complete installation instructions using Conda
- **[Conda Setup](CONDA_SETUP.md)** - Detailed Conda environment setup and configuration
- **[Python Setup](PYTHON_SETUP.md)** - Python installation check and configuration guide

### Usage Guides
- **[CLI Usage](CLI_USAGE.md)** - Complete command-line interface usage guide
- **[Download Guide](DOWNLOAD_GUIDE.md)** - SEC EDGAR filing download instructions

### Technical Documentation
- **[Neo4j Schema](neo4j_schema.md)** - Graph database schema documentation

## Quick Links

### Installation
```bash
# Quick setup
./setup_conda.sh
conda activate orion
```

### Common Commands
```bash
# Download SEC filings
python -m src.cli download --start-year 2009 --end-year 2010

# Setup database
python -m src.cli setup-db

# Test connections
python -m src.cli test-db --neo4j
```

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── INSTALLATION.md        # Installation guide
├── CONDA_SETUP.md         # Conda-specific setup
├── PYTHON_SETUP.md        # Python configuration
├── CLI_USAGE.md           # CLI command reference
├── DOWNLOAD_GUIDE.md      # SEC EDGAR download guide
├── ARCHITECTURE.md        # System architecture
├── DEVELOPMENT.md         # Development guide
└── neo4j_schema.md        # Database schema
```

## Contributing

When adding new documentation:
1. Place all documentation files in this `docs/` directory
2. Update this README.md with links to new documentation
3. Update the main README.md if needed
4. Keep documentation organized by topic

## Need Help?

- Check the [Installation Guide](INSTALLATION.md) for setup issues
- See [CLI Usage](CLI_USAGE.md) for command reference
- Review [Python Setup](PYTHON_SETUP.md) for Python configuration issues

