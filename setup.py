"""
Setup script for Orion project initialization.
This script helps set up the development environment.
"""

import os
import sys
import subprocess


def check_python_version():
    """Check if Python version is 3.9 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("✗ Python 3.9+ is required. Current version:", sys.version)
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


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


def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("\nInstalling Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Orion Project Setup")
    print("=" * 60)
    
    if not check_python_version():
        sys.exit(1)
    
    create_env_file()
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Update .env file with your database credentials")
    print("2. Set up Neo4j:")
    print("   - Option A: Sign up for Neo4j Aura Free at https://neo4j.com/cloud/aura-free/")
    print("   - Option B: Install Neo4j Desktop or use Docker")
    print("3. Set up Ollama or LM Studio:")
    print("   - Ollama: https://ollama.ai/")
    print("   - LM Studio: https://lmstudio.ai/")
    print("4. Initialize Neo4j schema:")
    print("   python src/database/neo4j_connection.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

