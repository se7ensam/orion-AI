# Installation Guide

## Important: Conda-Only Setup

**This project uses Conda exclusively for dependency management.** 

- ✅ Use `conda env create -f environment.yml` or `./setup_conda.sh`
- ❌ Do NOT use `pip install -r requirements.txt`
- ❌ Do NOT use `python -m venv` or virtualenv

All Python packages are managed through the conda environment defined in `environment.yml`.

## Quick Installation

### Step 1: Install Conda

If you don't have Conda installed:

- **Miniconda** (recommended): https://docs.conda.io/en/latest/miniconda.html
- **Anaconda**: https://www.anaconda.com/products/distribution

### Step 2: Create Environment

**Option A: Using Setup Script (Recommended)**
```bash
./setup_conda.sh
conda activate orion
```

**Option B: Manual Setup**
```bash
conda env create -f environment.yml
conda activate orion
```

### Step 3: Verify Installation

```bash
# Check environment is active
conda info --envs

# Test CLI
python -m src.cli --help

# Test database connection (if configured)
python -m src.cli test-db --neo4j
```

## What Gets Installed

The conda environment includes:

- **Python** >= 3.9
- **12 Python packages** via pip (managed by conda):
  - Core: python-dotenv
  - Database: neo4j, oracledb
  - LangChain: langchain, langchain-community, langchain-core, langchain-neo4j, langchain-ollama
  - Utilities: pyyaml
  - SEC Ingestion: requests, beautifulsoup4, tqdm

## Updating Dependencies

If `environment.yml` is updated:

```bash
conda activate orion
conda env update -f environment.yml --prune
```

## Troubleshooting

### Environment Already Exists
```bash
# Remove and recreate
conda env remove -n orion
conda env create -f environment.yml
```

### Missing Packages
```bash
conda activate orion
conda env update -f environment.yml --prune
```

### Conda Not Found
Make sure Conda is in your PATH. After installation, restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Why Conda Only?

- Consistent environment across all systems
- Better handling of binary dependencies
- Isolated from system Python
- Easier to manage complex dependencies
- Standard practice for data science projects

## Next Steps

After installation:

1. Configure `.env` file with database credentials
2. Setup Neo4j: `python -m src.cli setup-db`
3. Test connections: `python -m src.cli test-db --neo4j`
4. Download data: `python -m src.cli download --start-year 2009 --end-year 2010`

