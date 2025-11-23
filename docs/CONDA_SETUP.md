# Conda Setup Guide

## Overview

Orion is fully configured for Conda. The project includes:
- ✅ `environment.yml` - Conda environment definition
- ✅ `setup_conda.sh` - Automated setup script
- ✅ All dependencies specified

## Quick Start

### Option 1: Using the Setup Script (Recommended)

```bash
./setup_conda.sh
conda activate orion
```

### Option 2: Manual Setup

```bash
# Create environment from environment.yml
conda env create -f environment.yml

# Activate environment
conda activate orion

# Verify installation
python -m src.cli test-db --neo4j
```

## Environment Details

- **Environment Name**: `orion`
- **Python Version**: >= 3.9
- **Channels**: conda-forge, defaults
- **Package Manager**: pip (for Python packages)

## Dependencies

### Conda Packages
- Python >= 3.9
- pip

### Pip Packages (12 total)
- **Core**: python-dotenv
- **Database**: neo4j, oracledb
- **LangChain**: langchain, langchain-community, langchain-core, langchain-neo4j, langchain-ollama
- **Utilities**: pyyaml
- **SEC Ingestion**: requests, beautifulsoup4, tqdm

## Verification

Check if the environment exists:
```bash
conda env list | grep orion
```

Activate and test:
```bash
conda activate orion
python -m src.cli --help
```

Check installed packages:
```bash
conda activate orion
pip list
```

## Updating the Environment

If you modify `environment.yml`:
```bash
conda env update -f environment.yml --prune
```

Or recreate from scratch:
```bash
conda env remove -n orion
conda env create -f environment.yml
```

## Troubleshooting

### Environment Already Exists
If the environment already exists, you can:
1. Remove and recreate: `conda env remove -n orion && conda env create -f environment.yml`
2. Update existing: `conda env update -f environment.yml --prune`

### Missing Packages
If packages are missing after setup, update the environment:
```bash
conda activate orion
conda env update -f environment.yml --prune
```

**Note:** All packages are managed through conda's pip section in `environment.yml`. The `requirements.txt` file is kept for reference only.

### Conda Not Found
Install Miniconda or Anaconda:
- Miniconda: https://docs.conda.io/en/latest/miniconda.html
- Anaconda: https://www.anaconda.com/products/distribution

## Current Status

✅ Conda is configured and ready to use
✅ Environment file is valid
✅ Setup script is available
✅ All dependencies are specified

