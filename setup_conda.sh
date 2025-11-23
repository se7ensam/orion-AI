#!/bin/bash
# Setup script for Orion project using Conda
# This script creates the conda environment and sets up the project

set -e  # Exit on error

echo "============================================================"
echo "Orion Project - Conda Setup"
echo "============================================================"
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Error: Conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda from:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✓ Conda found: $(conda --version)"
echo ""

# Verify we're using conda Python, not system/Homebrew Python
CURRENT_PYTHON=$(which python 2>/dev/null || which python3)
if [[ "$CURRENT_PYTHON" != *"conda"* ]] && [[ "$CURRENT_PYTHON" != *"miniconda"* ]] && [[ "$CURRENT_PYTHON" != *"anaconda"* ]]; then
    echo "⚠️  Warning: Current Python is not from conda: $CURRENT_PYTHON"
    echo "   This may cause issues. Please ensure conda is initialized in your shell."
    echo "   Run: conda init $(basename $SHELL)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Using conda Python: $CURRENT_PYTHON"
fi
echo ""

# Check if environment.yml exists
if [ ! -f "environment.yml" ]; then
    echo "❌ Error: environment.yml not found"
    exit 1
fi

# Create conda environment
echo "Creating conda environment 'orion' from environment.yml..."
conda env create -f environment.yml

echo ""
echo "✓ Conda environment 'orion' created successfully"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# Neo4j Aura Free (if using cloud)
# NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_aura_password

# Oracle AI Vector DB Configuration
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=your_host:1521/your_service

# Ollama Configuration (if using local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# LM Studio Configuration (alternative to Ollama)
# LM_STUDIO_BASE_URL=http://localhost:1234/v1

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
EOF
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Activate the conda environment:"
echo "   conda activate orion"
echo ""
echo "2. Update .env file with your database credentials"
echo ""
echo "3. Setup Neo4j database:"
echo "   python -m src.cli setup-db"
echo ""
echo "4. Test the setup:"
echo "   python -m src.cli test-db --neo4j"
echo ""
echo "5. Download SEC filings:"
echo "   python -m src.cli download --start-year 2009 --end-year 2010"
echo ""

