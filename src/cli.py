#!/usr/bin/env python3
"""
Orion CLI - Main command-line interface for the Orion document management system.

Usage:
    python -m src.cli <command> [options]
    
Commands:
    download      Download SEC EDGAR filings
    setup-db      Initialize Neo4j database schema
    test-db       Test database connections
    test          Run test suite
    
Examples:
    # Download SEC filings
    python -m src.cli download --start-year 2009 --end-year 2010
    
    # Setup Neo4j database
    python -m src.cli setup-db
    
    # Test database connections
    python -m src.cli test-db --neo4j
"""

import sys
import os
import argparse
from typing import Optional


def download_command(args):
    """Handle download command - uses Node.js downloader for better I/O."""
    import subprocess
    from pathlib import Path
    
    if args.start_year > args.end_year:
        print("❌ Error: start_year must be <= end_year")
        sys.exit(1)
    
    if args.start_year < 1994:
        print("⚠️  Warning: SEC EDGAR data may not be available before 1994")
    
    # Get path to TypeScript downloader service
    # Try multiple possible locations (local dev vs Docker)
    project_root = Path(__file__).parent.parent.parent
    possible_paths = [
        # Local development path
        project_root / "services" / "downloader" / "dist" / "index.js",
        # Docker container path
        Path("/app") / "services" / "downloader" / "dist" / "index.js",
    ]
    
    downloader_js = None
    for path in possible_paths:
        if path.exists():
            downloader_js = path
            break
    
    if not downloader_js:
        downloader_service = project_root / "services" / "downloader"
        print("❌ Error: Downloader service not found")
        print(f"   Tried paths:")
        for path in possible_paths:
            print(f"     - {path}")
        print("\n   Please build the service:")
        print(f"   cd {downloader_service} && npm install && npm run build")
        sys.exit(1)
    
    # Build command arguments
    cmd = ["node", str(downloader_js)]
    cmd.append(str(args.start_year))
    cmd.append(str(args.end_year))
    
    if args.no_skip_existing:
        cmd.append("--no-skip-existing")
    
    if args.download_dir:
        cmd.extend(["--download-dir", args.download_dir])
    
    if args.max_workers:
        cmd.extend(["--max-workers", str(args.max_workers)])
    
    # Set environment variable for data directory
    import os
    env = os.environ.copy()
    if args.download_dir:
        env["ORION_DATA_DIR"] = os.path.dirname(args.download_dir)
    
    # Run Node.js downloader
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Download failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Node.js not found")
        print("   Please install Node.js: https://nodejs.org/")
        sys.exit(1)


def setup_db_command(args):
    """Handle setup-db command."""
    from src.database.neo4j_connection import Neo4jConnection
    
    print("=" * 60)
    print("Neo4j Database Setup")
    print("=" * 60)
    print()
    
    conn = Neo4jConnection()
    
    if conn.connect():
        try:
            conn.test_connection()
            conn.setup_schema()
            print()
            print("✅ Database setup completed successfully!")
        except Exception as e:
            print(f"\n❌ Error setting up database: {e}")
            sys.exit(1)
        finally:
            conn.close()
    else:
        print("\n❌ Failed to connect to Neo4j.")
        print("Please check your .env file and ensure Neo4j is running.")
        print("For Neo4j Aura Free, update NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env")
        sys.exit(1)


def test_db_command(args):
    """Handle test-db command."""
    if args.neo4j or not args.oracle:
        print("=" * 60)
        print("Testing Neo4j Connection")
        print("=" * 60)
        from src.database.neo4j_connection import Neo4jConnection
        
        conn = Neo4jConnection()
        if conn.connect():
            if conn.test_connection():
                print("✅ Neo4j connection test passed!")
            else:
                print("❌ Neo4j connection test failed!")
                sys.exit(1)
            conn.close()
        else:
            print("❌ Failed to connect to Neo4j")
            sys.exit(1)
        print()
    
    if args.oracle or not args.neo4j:
        print("=" * 60)
        print("Testing Oracle AI Vector DB Connection")
        print("=" * 60)
        from src.database.oracle_connection import OracleConnection
        
        conn = OracleConnection()
        if conn.connect():
            if conn.test_connection():
                print("✅ Oracle AI Vector DB connection test passed!")
            else:
                print("❌ Oracle AI Vector DB connection test failed!")
                sys.exit(1)
            conn.close()
        else:
            print("❌ Failed to connect to Oracle AI Vector DB")
            sys.exit(1)


def test_command(args):
    """Handle test command."""
    import subprocess
    
    print("=" * 60)
    print("Running Tests")
    print("=" * 60)
    print()
    
    # Run the test download script
    if args.download:
        print("🧪 Testing SEC EDGAR downloader...")
        print()
        try:
            result = subprocess.run(
                [sys.executable, "test_download.py"],
                check=False,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            if result.returncode == 0:
                print("\n✅ Download test passed!")
            else:
                print(f"\n❌ Download test failed with exit code {result.returncode}")
                sys.exit(1)
        except FileNotFoundError:
            print("❌ test_download.py not found!")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error running test: {e}")
            sys.exit(1)
    else:
        print("No tests specified. Use --download to test the downloader.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orion - Document Management & Knowledge Graph System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download SEC EDGAR filings
  python -m src.cli download --start-year 2009 --end-year 2010
  
  # Setup Neo4j database
  python -m src.cli setup-db
  
  # Test database connections
  python -m src.cli test-db --neo4j
  python -m src.cli test-db --oracle
  
  # Run tests
  python -m src.cli test --download
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True
    
    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download SEC EDGAR 6-K filings",
        description="Download SEC EDGAR 6-K filings for Foreign Private Issuers"
    )
    download_parser.add_argument(
        "--start-year",
        type=int,
        default=2009,
        help="Starting year (inclusive, default: 2009)"
    )
    download_parser.add_argument(
        "--end-year",
        type=int,
        default=2010,
        help="Ending year (inclusive, default: 2010)"
    )
    download_parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-download filings even if they already exist"
    )
    download_parser.add_argument(
        "--download-dir",
        type=str,
        default=None,
        help="Custom download directory (default: data/edgar_filings)"
    )
    download_parser.add_argument(
        "--max-workers",
        type=int,
        default=200,
        help="Number of parallel workers for downloads (default: 200, recommended: 200-500 for max speed)"
    )
    download_parser.set_defaults(func=download_command)
    
    # Setup DB command
    setup_db_parser = subparsers.add_parser(
        "setup-db",
        help="Initialize Neo4j database schema",
        description="Set up Neo4j database with indexes and constraints"
    )
    setup_db_parser.set_defaults(func=setup_db_command)
    
    # Test DB command
    test_db_parser = subparsers.add_parser(
        "test-db",
        help="Test database connections",
        description="Test connections to Neo4j and/or Oracle AI Vector DB"
    )
    test_db_parser.add_argument(
        "--neo4j",
        action="store_true",
        help="Test Neo4j connection only"
    )
    test_db_parser.add_argument(
        "--oracle",
        action="store_true",
        help="Test Oracle AI Vector DB connection only"
    )
    test_db_parser.set_defaults(func=test_db_command)
    
    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Run test suite",
        description="Run various tests to verify system functionality"
    )
    test_parser.add_argument(
        "--download",
        action="store_true",
        help="Test SEC EDGAR downloader"
    )
    test_parser.set_defaults(func=test_command)
    
    args = parser.parse_args()
    
    # Execute the command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

