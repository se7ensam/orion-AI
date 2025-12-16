#!/usr/bin/env python3
"""
Orion CLI - Main command-line interface for the Orion document management system.

Usage:
    python -m services.cli.main <command> [options]
    
Commands:
    download      Download SEC EDGAR filings
    setup-db      Initialize Neo4j database schema
    test-db       Test database connections
    test          Run test suite
    
Examples:
    # Download SEC filings
    python -m services.cli.main download --start-year 2009 --end-year 2010
    
    # Setup Neo4j database
    python -m services.cli.main setup-db
    
    # Test database connections
    python -m services.cli.main test-db --neo4j
"""

import sys
import os
import json
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
    from services.database.neo4j_connection import Neo4jConnection
    
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
        from services.database.neo4j_connection import Neo4jConnection
        
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
        from services.database.oracle_connection import OracleConnection
        
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
    from services.database.neo4j_connection import Neo4jConnection
    from services.graph_builder.graph_builder import GraphBuilder
    
    print("=" * 60)
    print("Loading EDGAR Filings into Neo4j Graph")
    print("=" * 60)
    print()
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    
    if not conn.connect():
        print("\n❌ Failed to connect to Neo4j.")
        print("Please check your .env file and ensure Neo4j is running.")
        print("For local Neo4j, run: make neo4j")
        sys.exit(1)
    
    try:
        # Setup schema if needed
        if not args.skip_schema:
            print("Setting up Neo4j schema...")
            conn.setup_schema()
            print()
        
        # Create graph builder (pattern-based extraction only)
        print("Using pattern-based relationship extraction")
        print()
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
        
        # Print timing information
        if 'total_time' in stats:
            total_time = stats['total_time']
            print("⏱️  Performance Metrics:")
            print(f"   Total time: {total_time:.2f}s")
            if stats['filings_processed'] > 0:
                avg_time = total_time / stats['filings_processed']
                print(f"   Average time per filing: {avg_time:.2f}s")
            
            if stats.get('pattern_extractions_count', 0) > 0:
                pattern_time = stats.get('pattern_extraction_time', 0)
                pattern_count = stats['pattern_extractions_count']
                avg_pattern_time = pattern_time / pattern_count if pattern_count > 0 else 0
                print(f"   Pattern extractions: {pattern_count} ({pattern_time:.2f}s total, {avg_pattern_time:.2f}s avg)")
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


def analyze_command(args):
    """Handle analyze command - AI-powered code analysis."""
    from services.ai.ai_analyzer import create_ai_analyzer, list_analysis_results, load_analysis_result, get_analysis_dir
    from services.data_loader.data_loader import get_filing_data, list_filings
    from pathlib import Path
    import inspect
    
    # Handle list command
    if args.list:
        print("=" * 60)
        print("Previous Analysis Results")
        print("=" * 60)
        print()
        
        results = list_analysis_results()
        
        if not results:
            print("No analysis results found.")
            return
        
        # Group by type
        by_type = {}
        for result in results:
            atype = result["analysis_type"]
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(result)
        
        for atype, items in sorted(by_type.items()):
            print(f"\n{atype.replace('_', ' ').title()} ({len(items)} results):")
            print("-" * 60)
            for item in items[:10]:  # Show latest 10 per type
                timestamp = item["timestamp"][:19] if item["timestamp"] else "Unknown"
                print(f"  {item['file']}")
                print(f"    Date: {timestamp}")
                if item.get("metadata"):
                    meta_str = ", ".join(f"{k}={v}" for k, v in list(item["metadata"].items())[:3])
                    if meta_str:
                        print(f"    {meta_str}")
                print()
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more results")
        print(f"\nUse --view <filename> to view a specific analysis")
        return
    
    # Handle view command
    if args.view:
        print("=" * 60)
        print(f"Viewing Analysis: {args.view}")
        print("=" * 60)
        print()
        
        analysis_dir = get_analysis_dir()
        filepath = analysis_dir / args.view
        
        if not filepath.exists():
            print(f"❌ Analysis file not found: {filepath}")
            return
        
        try:
            data = load_analysis_result(filepath)
            print(f"**Type**: {data.get('analysis_type', 'Unknown')}")
            print(f"**Date**: {data.get('timestamp', 'Unknown')}")
            if data.get('metadata'):
                print(f"**Metadata**: {json.dumps(data['metadata'], indent=2)}")
            print()
            print("=" * 60)
            print("Analysis Content")
            print("=" * 60)
            print()
            
            result = data.get('result', {})
            if 'analysis' in result:
                print(result['analysis'])
            elif 'suggestions' in result:
                print(result['suggestions'])
            elif 'missing_entities' in result:
                print(result['missing_entities'])
            elif 'improvements' in result:
                print(result['improvements'])
            else:
                print(json.dumps(result, indent=2))
            
            # Also show markdown file if it exists
            md_file = filepath.with_suffix('.md')
            if md_file.exists():
                print()
                print(f"📄 Markdown version available at: {md_file}")
        except Exception as e:
            print(f"❌ Error loading analysis: {e}")
        return
    
    print("=" * 60)
    print("AI-Powered Graph Builder Analysis")
    print("=" * 60)
    print()
    
    # Initialize AI analyzer
    print("Initializing AI analyzer...")
    analyzer = create_ai_analyzer()
    
    if not analyzer.is_available():
        print("❌ AI analyzer not available. Make sure Ollama is running:")
        print("   brew services start ollama")
        print("   ollama pull llama3.2")
        return
    
    print("✅ AI analyzer ready")
    print()
    
    # Read graph builder code
    print("Reading graph builder code...")
    graph_builder_path = Path(__file__).parent.parent / "src" / "graph_builder.py"
    
    if not graph_builder_path.exists():
        print(f"❌ Could not find graph_builder.py at {graph_builder_path}")
        return
    
    with open(graph_builder_path, 'r') as f:
        code_content = f.read()
    
    print(f"✅ Loaded {len(code_content)} characters of code")
    print()
    
    # Load sample filings
    print(f"Loading sample filings (limit: {args.limit})...")
    year = args.year or 2010
    filings = list_filings(year=year)
    
    if not filings:
        print(f"❌ No filings found for year {year}")
        return
    
    sample_filings = []
    for filing_path in filings[:args.limit]:
        try:
            filing_data = get_filing_data(filing_path)
            sample_filings.append(filing_data)
            print(f"  ✅ Loaded: {filing_path.name}")
        except Exception as e:
            print(f"  ⚠️  Error loading {filing_path.name}: {e}")
    
    if not sample_filings:
        print("❌ No valid filings loaded")
        return
    
    print(f"✅ Loaded {len(sample_filings)} sample filings")
    print()
    
    # Run analysis
    print("=" * 60)
    print("Running AI Analysis...")
    print("=" * 60)
    print()
    
    # Main code analysis
    print("📊 Analyzing parsing logic...")
    result = analyzer.analyze_parsing_logic(code_content, sample_filings)
    
    if result.get("status") == "success":
        # Save analysis result
        from services.ai.ai_analyzer import save_analysis_result
        metadata = {
            "year": year,
            "limit": args.limit,
            "filings_analyzed": len(sample_filings)
        }
        saved_path = save_analysis_result("parsing_logic", result, metadata)
        print(f"💾 Analysis saved to: {saved_path}")
        print()
        
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print()
        print(result["analysis"])
        print()
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    # Pattern analysis if requested
    if args.patterns:
        print("\n" + "=" * 60)
        print("PATTERN SUGGESTIONS")
        print("=" * 60)
        print()
        
        # Extract current patterns from code
        import re
        pattern_matches = re.findall(r'r[\'"]([^\'"]+)[\'"]', code_content)
        
        # Get sample content
        sample_content = ""
        for filing in sample_filings[:2]:
            sample_content += (filing.get('raw_text', '') + filing.get('html_content', ''))[:3000]
        
        pattern_result = analyzer.suggest_extraction_patterns(sample_content, pattern_matches[:10])
        
        if pattern_result.get("status") == "success":
            # Save pattern analysis
            from services.ai.ai_analyzer import save_analysis_result
            metadata = {
                "year": year,
                "limit": args.limit,
                "patterns_analyzed": len(pattern_matches[:10])
            }
            saved_path = save_analysis_result("patterns", pattern_result, metadata)
            print(f"💾 Pattern analysis saved to: {saved_path}")
            print()
            
            print(pattern_result["suggestions"])
        else:
            print(f"❌ Pattern analysis failed: {pattern_result.get('error')}")
        print()
    
    # Missing entities analysis if requested
    if args.missing:
        print("\n" + "=" * 60)
        print("MISSING ENTITIES ANALYSIS")
        print("=" * 60)
        print()
        
        # Process one filing to get extracted entities
        from services.database.neo4j_connection import Neo4jConnection
        from services.graph_builder.graph_builder import GraphBuilder
        
        conn = Neo4jConnection()
        if conn.connect():
            builder = GraphBuilder(conn)
            
            # Extract entities from first filing
            filing_data = sample_filings[0]
            people = builder.extract_people_from_filing(filing_data)
            events = builder.extract_events_from_filing(filing_data)
            
            extracted = {
                "people": [{"name": p.get("name"), "title": p.get("title")} for p in people],
                "events": [{"type": e.get("event_type"), "title": e.get("title")} for e in events],
                "company": {
                    "name": filing_data.get("company_name"),
                    "cik": filing_data.get("cik")
                }
            }
            
            content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
            missing_result = analyzer.analyze_missing_entities(content[:8000], extracted)
            
            if missing_result.get("status") == "success":
                # Save missing entities analysis
                from services.ai.ai_analyzer import save_analysis_result
                metadata = {
                    "year": year,
                    "filing_cik": filing_data.get("cik"),
                    "extracted_people": len(people),
                    "extracted_events": len(events)
                }
                saved_path = save_analysis_result("missing_entities", missing_result, metadata)
                print(f"💾 Missing entities analysis saved to: {saved_path}")
                print()
                
                print(missing_result["missing_entities"])
            else:
                print(f"❌ Missing entities analysis failed: {missing_result.get('error')}")
            
            conn.close()
        print()
    
    # Schema suggestions if requested
    if args.schema:
        print("\n" + "=" * 60)
        print("GRAPH SCHEMA SUGGESTIONS")
        print("=" * 60)
        print()
        
        # Get current schema info
        current_schema = {
            "nodes": ["Company", "Person", "Event", "Sector"],
            "relationships": ["OWNS", "SUBSIDIARY_OF", "WORKS_AT", "HAS_EVENT", "BELONGS_TO_SECTOR"]
        }
        
        # Process filings to get extracted data
        from services.database.neo4j_connection import Neo4jConnection
        from services.graph_builder.graph_builder import GraphBuilder
        
        conn = Neo4jConnection()
        if conn.connect():
            builder = GraphBuilder(conn)
            
            # Sample extracted data
            sample_data = {
                "companies": [{"cik": f.get("cik"), "name": f.get("company_name")} for f in sample_filings[:3]],
                "people_count": sum(len(builder.extract_people_from_filing(f)) for f in sample_filings[:3])
            }
            
            schema_result = analyzer.suggest_graph_improvements(current_schema, sample_data)
            
            if schema_result.get("status") == "success":
                # Save schema analysis
                from services.ai.ai_analyzer import save_analysis_result
                metadata = {
                    "year": year,
                    "limit": args.limit,
                    "sample_companies": len(sample_data.get("companies", []))
                }
                saved_path = save_analysis_result("schema", schema_result, metadata)
                print(f"💾 Schema analysis saved to: {saved_path}")
                print()
                
                print(schema_result["improvements"])
            else:
                print(f"❌ Schema analysis failed: {schema_result.get('error')}")
            
            conn.close()
        print()
    
    print("=" * 60)
    print("Analysis Complete")
    print("=" * 60)


def query_command(args):
    """Handle query command - Natural language to Cypher query conversion."""
    from services.ai.cypher_rag import CypherRAG
    from services.database.neo4j_connection import Neo4jConnection
    
    print("=" * 80)
    print("Cypher RAG - Natural Language Query")
    print("=" * 80)
    print()
    
    # Initialize Cypher RAG
    print("Initializing Cypher RAG service...")
    try:
        rag = CypherRAG(model_name=args.model if args.model else "llama3.2")
        if not rag.is_available():
            print("❌ Cypher RAG is not available. Please ensure Ollama is running.")
            print("   Start Ollama: docker-compose up -d ollama")
            return
        print("✓ Cypher RAG initialized")
    except Exception as e:
        print(f"❌ Error initializing Cypher RAG: {e}")
        return
    
    # Connect to Neo4j
    print("\nConnecting to Neo4j...")
    conn = Neo4jConnection()
    if not conn.connect():
        print("❌ Failed to connect to Neo4j")
        return
    print("✓ Connected to Neo4j")
    
    try:
        # Get query from args or prompt
        if args.query:
            natural_query = args.query
        else:
            # Interactive mode
            print("\n" + "=" * 80)
            print("Interactive Query Mode (type 'exit' to quit)")
            print("=" * 80)
            while True:
                natural_query = input("\n💬 Enter your question: ").strip()
                if not natural_query or natural_query.lower() in ['exit', 'quit', 'q']:
                    break
                
                if args.show_cypher:
                    print(f"\n📝 Natural Language Query: {natural_query}")
                
                # Generate and execute query
                print("\n🤖 Generating Cypher query...")
                results, error, cypher_query = rag.query_with_retry(
                    natural_query,
                    conn,
                    max_retries=2
                )
                
                if error:
                    print(f"\n❌ Error: {error}")
                    if args.show_cypher and cypher_query:
                        print(f"\nGenerated Cypher query:\n{cypher_query}")
                    continue
                
                # Show Cypher query if requested
                if args.show_cypher:
                    print(f"\n✅ Generated Cypher Query:")
                    print("-" * 80)
                    print(cypher_query)
                    print("-" * 80)
                
                # Display results
                if results:
                    formatted = rag.format_results(results, max_rows=args.max_rows)
                    print(formatted)
                else:
                    print("\nNo results found.")
        
        # Non-interactive mode (single query)
        if args.query:
            if args.show_cypher:
                print(f"\n📝 Natural Language Query: {natural_query}")
            
            print("\n🤖 Generating Cypher query...")
            results, error, cypher_query = rag.query_with_retry(
                natural_query,
                conn,
                max_retries=2
            )
            
            if error:
                print(f"\n❌ Error: {error}")
                if args.show_cypher and cypher_query:
                    print(f"\nGenerated Cypher query:\n{cypher_query}")
                return
            
            # Show Cypher query if requested
            if args.show_cypher:
                print(f"\n✅ Generated Cypher Query:")
                print("-" * 80)
                print(cypher_query)
                print("-" * 80)
            
            # Display results
            if results:
                formatted = rag.format_results(results, max_rows=args.max_rows)
                print(formatted)
            else:
                print("\nNo results found.")
    
    finally:
        conn.close()


def clear_graph_command(args):
    """Handle clear-graph command."""
    from services.database.neo4j_connection import Neo4jConnection
    
    if not args.confirm:
        print("=" * 60)
        print("⚠️  WARNING: Clear Neo4j Graph Database")
        print("=" * 60)
        print()
        print("This will DELETE ALL nodes and relationships from Neo4j.")
        print("The schema (constraints and indexes) will be preserved.")
        print()
        print("To confirm, run:")
        print("  python -m services.cli.main clear-graph --confirm")
        print()
        sys.exit(1)
    
    print("=" * 60)
    print("Clearing Neo4j Graph Database")
    print("=" * 60)
    print()
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    
    if not conn.connect():
        print("\n❌ Failed to connect to Neo4j.")
        print("Please check your .env file and ensure Neo4j is running.")
        print("For local Neo4j, run: make neo4j")
        sys.exit(1)
    
    try:
        # Count nodes before deletion
        result = conn.execute_query("MATCH (n) RETURN count(n) as count")
        node_count = result[0]['count'] if result else 0
        
        result = conn.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result[0]['count'] if result else 0
        
        print(f"Current graph state:")
        print(f"  Nodes: {node_count}")
        print(f"  Relationships: {rel_count}")
        print()
        
        if node_count == 0:
            print("✅ Graph is already empty.")
            return
        
        print("Deleting all nodes and relationships...")
        
        # Delete all relationships first, then nodes
        conn.execute_query("MATCH ()-[r]->() DELETE r")
        conn.execute_query("MATCH (n) DELETE n")
        
        print("✅ All nodes and relationships deleted.")
        print()
        print("Schema (constraints and indexes) is preserved.")
        print("You can now reload data with: python -m services.cli.main load-graph")
        
    except Exception as e:
        print(f"\n❌ Error clearing graph: {e}")
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
  python -m services.cli.main download --start-year 2009 --end-year 2010
  
  # Setup Neo4j database schema
  python -m services.cli.main setup-db
  
  # Clear Neo4j graph (requires --confirm)
  python -m services.cli.main clear-graph --confirm
  
  # Load filings into Neo4j graph
  python -m services.cli.main load-graph --year 2009 --limit 10
  python -m services.cli.main load-graph --year 2009
  
  # Test database connections
  python -m services.cli.main test-db --neo4j
  python -m services.cli.main test-db --oracle
  
  # Run tests
  python -m services.cli.main test --download
  
  # Query graph with natural language
  python -m services.cli.main query "Find all companies"
  python -m services.cli.main query "Who works at Apple Inc?" --show-cypher
  python -m services.cli.main query  # Interactive mode
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
    
    # Clear Graph command
    clear_graph_parser = subparsers.add_parser(
        "clear-graph",
        help="Clear all data from Neo4j graph database",
        description="Delete all nodes and relationships from Neo4j (keeps schema intact)"
    )
    clear_graph_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion (required to prevent accidental deletion)"
    )
    clear_graph_parser.set_defaults(func=clear_graph_command)
    
    # Analyze command - AI-powered code analysis
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="AI-powered analysis of graph builder parsing logic",
        description="Analyze the graph builder code and suggest improvements based on actual filing data"
    )
    analyze_parser.add_argument(
        "--year",
        type=int,
        help="Year of filings to analyze (default: 2010)"
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of sample filings to analyze (default: 5)"
    )
    analyze_parser.add_argument(
        "--patterns",
        action="store_true",
        help="Analyze and suggest improved regex patterns"
    )
    analyze_parser.add_argument(
        "--missing",
        action="store_true",
        help="Find missing entities in extracted data"
    )
    analyze_parser.add_argument(
        "--schema",
        action="store_true",
        help="Suggest graph schema improvements"
    )
    analyze_parser.add_argument(
        "--list",
        action="store_true",
        help="List all previous analysis results"
    )
    analyze_parser.add_argument(
        "--view",
        type=str,
        metavar="FILENAME",
        help="View a specific analysis result (filename from --list)"
    )
    analyze_parser.set_defaults(func=analyze_command)
    
    # Query command - Natural language to Cypher
    query_parser = subparsers.add_parser(
        "query",
        help="Query Neo4j graph using natural language",
        description="Convert natural language questions to Cypher queries and execute them"
    )
    query_parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="Natural language query (if not provided, enters interactive mode)"
    )
    query_parser.add_argument(
        "--show-cypher",
        action="store_true",
        help="Show the generated Cypher query"
    )
    query_parser.add_argument(
        "--max-rows",
        type=int,
        default=50,
        help="Maximum number of rows to display (default: 50)"
    )
    query_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model to use (default: llama3.2)"
    )
    query_parser.set_defaults(func=query_command)
    
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

