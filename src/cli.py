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
    project_root = Path(__file__).parent.parent  # src/cli.py -> src -> orion/
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
    
    if args.use_multi_ip:
        cmd.append("--use-multi-ip")
    
    if args.max_filings:
        cmd.extend(["--max-filings", str(args.max_filings)])
    
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


def load_graph_command(args):
    """Handle load-graph command."""
    from src.database.neo4j_connection import Neo4jConnection
    from src.graph_builder import GraphBuilder
    
    print("=" * 60)
    print("Loading EDGAR Filings into Neo4j Graph")
    print("=" * 60)
    print()
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    
    if not conn.connect():
        print("\n❌ Failed to connect to Neo4j.")
        print("Please check your .env file and ensure Neo4j is running.")
        print("For local Neo4j, run: cd neo4j && docker-compose up -d")
        sys.exit(1)
    
    try:
        # Setup schema if needed
        if not args.skip_schema:
            print("Setting up Neo4j schema...")
            conn.setup_schema()
            print()
        
        # Create graph builder
        builder = GraphBuilder(conn)
        
        # Process filings
        year_str = f" for year {args.year}" if args.year else ""
        limit_str = f" (limited to {args.limit} filings)" if args.limit else ""
        print(f"Processing filings{year_str}{limit_str}...")
        print()
        
        stats = builder.process_filings(year=args.year, limit=args.limit)
        
        # Print results
        print()
        print("=" * 60)
        print("Graph Loading Complete")
        print("=" * 60)
        print(f"✅ Companies created: {stats['companies']}")
        print(f"✅ People created: {stats['people']}")
        print(f"✅ Events created: {stats['events']}")
        print(f"✅ Relationships created: {stats['relationships']}")
        print(f"✅ Filings processed: {stats['filings_processed']}")
        print()
        print("Graph is ready for querying!")
        print()
        print("Example queries:")
        print("  MATCH (c:Company) RETURN c.name LIMIT 10")
        print("  MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p.name, c.name LIMIT 10")
        print("  MATCH (c:Company)-[:HAS_EVENT]->(e:Event) RETURN c.name, e.title LIMIT 10")
        
    except Exception as e:
        print(f"\n❌ Error loading graph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orion - Document Management & Knowledge Graph System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download SEC EDGAR filings
  python -m src.cli download --start-year 2009 --end-year 2010
  
  # Setup Neo4j database schema
  python -m src.cli setup-db
  
  # Load filings into Neo4j graph
  python -m src.cli load-graph --year 2009 --limit 10
  python -m src.cli load-graph --year 2009
  
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
        default=100,
        help="Number of parallel workers for downloads (default: 100, rate limiter ensures SEC compliance)"
    )
    download_parser.add_argument(
        "--use-multi-ip",
        action="store_true",
        help="Enable multi-IP parallel processing for faster downloads (requires IP_PROXIES environment variable)"
    )
    download_parser.add_argument(
        "--max-filings",
        type=int,
        default=None,
        help="Maximum number of filings to download (useful for testing, e.g., --max-filings 1000)"
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
    
    # Load Graph command
    load_graph_parser = subparsers.add_parser(
        "load-graph",
        help="Load EDGAR filings into Neo4j graph database",
        description="Process EDGAR filings and build graph with entities and relationships"
    )
    load_graph_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Process filings for specific year (e.g., 2009). If not specified, processes all years."
    )
    load_graph_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of filings to process (useful for testing, e.g., --limit 10)"
    )
    load_graph_parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Skip schema setup (use if schema already exists)"
    )
    load_graph_parser.set_defaults(func=load_graph_command)
    
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

