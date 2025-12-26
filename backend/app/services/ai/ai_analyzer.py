"""
AI Code Analyzer for Graph Builder Logic

Uses AI to analyze the graph builder parsing logic and suggest improvements
based on actual filing data.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


class GraphBuilderAnalyzer:
    """AI-powered analyzer for graph builder logic improvements."""
    
    def __init__(self, model_name: str = "llama3.2", base_url: Optional[str] = None):
        """
        Initialize AI analyzer.
        
        Args:
            model_name: Name of the Ollama model to use (default: "llama3.2")
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        self.llm = None
        
        # Ensure model is available
        self._ensure_model_available()
        
        # Initialize LLM
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.1,  # Lower temperature for more consistent analysis
                num_ctx=4096  # Larger context for code analysis
            )
        except Exception as e:
            print(f"Warning: Could not initialize AI analyzer: {e}")
            self.llm = None
    
    def _ensure_model_available(self):
        """Check if model is available, download if not."""
        try:
            # Check if model exists
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.model_name not in result.stdout:
                print(f"Model {self.model_name} not found. Downloading...")
                subprocess.run(
                    ["ollama", "pull", self.model_name],
                    timeout=300
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Warning: Could not check/download model: {e}")
    
    def is_available(self) -> bool:
        """Check if AI analyzer is available."""
        return self.llm is not None
    
    def analyze_parsing_logic(self, code_content: str, sample_filings: List[Dict]) -> Dict:
        """
        Analyze the graph builder parsing logic and suggest improvements.
        
        Args:
            code_content: The source code of graph_builder.py
            sample_filings: List of sample filing data dictionaries
            
        Returns:
            Dictionary with analysis results and suggestions
        """
        if not self.llm:
            return {"error": "AI analyzer not available"}
        
        # Prepare sample filing summaries
        filing_summaries = []
        for filing in sample_filings[:5]:  # Limit to 5 samples
            summary = {
                "cik": filing.get("cik", ""),
                "company_name": filing.get("company_name", ""),
                "filing_type": filing.get("filing_type", ""),
                "content_preview": (filing.get("raw_text", "") + filing.get("html_content", ""))[:2000],
                "has_people": bool(filing.get("raw_text", "") or filing.get("html_content", "")),
            }
            filing_summaries.append(summary)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code reviewer specializing in data extraction and graph database design.

Your task is to analyze Python code that parses SEC EDGAR filings and extracts entities (companies, people, events) 
to build a Neo4j graph database.

Analyze the code logic and suggest improvements based on:
1. Pattern matching effectiveness (regex patterns)
2. Missing entity types or relationships
3. Data quality issues (empty fields, incorrect parsing)
4. Edge cases not handled
5. Performance optimizations
6. Better extraction patterns

Provide specific, actionable suggestions with code examples when possible."""),
            ("human", """Analyze this graph builder code:

{code_content}

Sample filings analyzed:
{filings}

Based on the code logic and sample filing data, provide:
1. **Current Logic Analysis**: What the code currently does well
2. **Issues Found**: Problems or limitations in the current approach
3. **Suggestions**: Specific improvements with code examples
4. **Missing Patterns**: Entities or relationships that might be missed
5. **Edge Cases**: Scenarios not currently handled
6. **Graph Structure**: Recommendations for better graph schema

Format your response as structured analysis with clear sections.""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "code_content": code_content[:15000],  # Limit code size
                "filings": json.dumps(filing_summaries, indent=2)
            })
            
            return {
                "analysis": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def suggest_extraction_patterns(self, filing_content: str, current_patterns: List[str]) -> Dict:
        """
        Suggest better regex patterns based on filing content.
        
        Args:
            filing_content: Sample filing content
            current_patterns: List of current regex patterns being used
            
        Returns:
            Dictionary with suggested patterns
        """
        if not self.llm:
            return {"error": "AI analyzer not available"}
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a regex pattern expert. Analyze filing content and suggest 
improved regex patterns for extracting person names, titles, and relationships.

Provide patterns that are:
- More accurate (fewer false positives)
- More comprehensive (catch more cases)
- Well-documented with examples"""),
            ("human", """Current patterns being used:
{current_patterns}

Sample filing content:
{content}

Suggest improved regex patterns for extracting:
1. Person names (executives, directors, signatories)
2. Job titles
3. Company relationships
4. Event information

For each pattern, provide:
- The regex pattern
- Explanation of what it matches
- Example matches from the content""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "current_patterns": "\n".join(current_patterns),
                "content": filing_content[:5000]  # Limit content size
            })
            
            return {
                "suggestions": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def analyze_missing_entities(self, filing_content: str, extracted_entities: Dict) -> Dict:
        """
        Analyze filing content to find entities that were missed.
        
        Args:
            filing_content: Full filing content
            extracted_entities: Dictionary of entities that were extracted
            
        Returns:
            Dictionary with missing entities and suggestions
        """
        if not self.llm:
            return {"error": "AI analyzer not available"}
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing SEC EDGAR filings. Identify all entities 
(people, companies, events, relationships) that should be extracted from the filing.

Compare what was extracted vs what should have been extracted."""),
            ("human", """Filing content:
{content}

Currently extracted entities:
{extracted}

Identify:
1. Missing people (names, titles, roles)
2. Missing companies or subsidiaries
3. Missing events or filings
4. Missing relationships
5. Data quality issues in extracted entities

Provide specific examples from the content.""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "content": filing_content[:8000],
                "extracted": json.dumps(extracted_entities, indent=2)
            })
            
            return {
                "missing_entities": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def suggest_graph_improvements(self, current_schema: Dict, sample_data: Dict) -> Dict:
        """
        Suggest improvements to the graph schema based on data patterns.
        
        Args:
            current_schema: Current graph schema description
            sample_data: Sample of extracted data
            
        Returns:
            Dictionary with schema improvement suggestions
        """
        if not self.llm:
            return {"error": "AI analyzer not available"}
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a graph database design expert. Analyze the current Neo4j schema 
and suggest improvements based on the actual data being stored.

Consider:
- Missing node types or properties
- Missing relationship types
- Better indexing strategies
- Data normalization opportunities
- Query performance improvements"""),
            ("human", """Current graph schema:
{schema}

Sample extracted data:
{data}

Suggest improvements to:
1. Node types and properties
2. Relationship types and properties
3. Indexes for better query performance
4. Data structure optimizations
5. Missing relationships that could be valuable""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "schema": json.dumps(current_schema, indent=2),
                "data": json.dumps(sample_data, indent=2)
            })
            
            return {
                "improvements": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }


def get_analysis_dir() -> Path:
    """Get the directory where analysis results are stored."""
    data_dir = os.getenv("ORION_DATA_DIR", "./data")
    analysis_dir = Path(data_dir) / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    return analysis_dir


def save_analysis_result(analysis_type: str, result: Dict, metadata: Optional[Dict] = None) -> Path:
    """
    Save analysis result to a file.
    
    Args:
        analysis_type: Type of analysis (e.g., "parsing_logic", "patterns", "missing_entities", "schema")
        result: Analysis result dictionary
        metadata: Optional metadata (year, limit, etc.)
        
    Returns:
        Path to the saved file
    """
    analysis_dir = get_analysis_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{analysis_type}_{timestamp}.json"
    filepath = analysis_dir / filename
    
    # Prepare data to save
    data = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": analysis_type,
        "metadata": metadata or {},
        "result": result
    }
    
    # Save JSON
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Also save as markdown for readability
    md_filepath = analysis_dir / f"{analysis_type}_{timestamp}.md"
    with open(md_filepath, 'w') as f:
        f.write(f"# {analysis_type.replace('_', ' ').title()} Analysis\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if metadata:
            f.write("## Metadata\n\n")
            for key, value in metadata.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n")
        f.write("## Results\n\n")
        if "analysis" in result:
            f.write(result["analysis"])
        elif "suggestions" in result:
            f.write(result["suggestions"])
        elif "missing_entities" in result:
            f.write(result["missing_entities"])
        elif "improvements" in result:
            f.write(result["improvements"])
        else:
            f.write(json.dumps(result, indent=2))
        f.write("\n")
    
    return filepath


def list_analysis_results(analysis_type: Optional[str] = None) -> List[Dict]:
    """
    List all saved analysis results.
    
    Args:
        analysis_type: Optional filter by analysis type
        
    Returns:
        List of analysis metadata dictionaries
    """
    analysis_dir = get_analysis_dir()
    
    if not analysis_dir.exists():
        return []
    
    results = []
    pattern = f"{analysis_type}_*.json" if analysis_type else "*.json"
    
    for filepath in sorted(analysis_dir.glob(pattern), reverse=True):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                results.append({
                    "file": filepath.name,
                    "path": str(filepath),
                    "timestamp": data.get("timestamp"),
                    "analysis_type": data.get("analysis_type"),
                    "metadata": data.get("metadata", {})
                })
        except Exception:
            continue
    
    return results


def load_analysis_result(filepath: Path) -> Dict:
    """Load a saved analysis result."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_ai_analyzer() -> GraphBuilderAnalyzer:
    """Factory function to create an AI analyzer instance."""
    return GraphBuilderAnalyzer()

