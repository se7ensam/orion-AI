"""
Setup script for Orion project initialization.
This script helps set up the development environment.

NOTE: This project uses Conda exclusively. Use setup_conda.sh instead.

For CLI commands, use:
    python -m src.cli <command>
"""

import os
import sys


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    if os.path.exists(".env"):
        print("✓ .env file already exists")
        return True
    
    print("\nCreating .env file from template...")
    env_template = """# Neo4j Configuration
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
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_template)
        print("✓ .env file created. Please update it with your credentials.")
        return True
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Orion Project Setup")
    print("=" * 60)
    print()
    print("⚠️  NOTE: This project uses Conda exclusively.")
    print("   Please use ./setup_conda.sh instead for full setup.")
    print()
    print("=" * 60)
    
    create_env_file()
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Run conda setup:")
    print("   ./setup_conda.sh")
    print("   conda activate orion")
    print()
    print("2. Update .env file with your database credentials")
    print()
    print("3. Set up Neo4j:")
    print("   - Option A: Sign up for Neo4j Aura Free at https://neo4j.com/cloud/aura-free/")
    print("   - Option B: Install Neo4j Desktop or use Docker")
    print()
    print("4. Set up Ollama or LM Studio:")
    print("   - Ollama: https://ollama.ai/")
    print("   - LM Studio: https://lmstudio.ai/")
    print()
    print("5. Initialize Neo4j schema:")
    print("   python -m src.cli setup-db")
    print("=" * 60)


if __name__ == "__main__":
    main()

