# AI-Powered Graph Builder Analyzer

The AI Analyzer uses Large Language Models (LLM) to analyze your graph builder parsing logic and suggest improvements based on actual filing data.

## Overview

Instead of using AI to extract data (which we removed), this tool uses AI to:
- **Analyze** your current parsing code
- **Review** actual filing data
- **Suggest** improvements to extraction patterns
- **Identify** missing entities or relationships
- **Recommend** better graph schema designs

## Prerequisites

1. **Ollama installed and running**:
   ```bash
   brew install ollama
   brew services start ollama
   ollama pull llama3.2
   ```

2. **Sample filings available** in `data/filings/`

## Storage

All analysis results are automatically saved to `data/analysis/` directory:
- **JSON format**: Machine-readable format with full metadata
- **Markdown format**: Human-readable format for easy review
- **Timestamped**: Each analysis gets a unique timestamp
- **Organized by type**: Separate files for parsing_logic, patterns, missing_entities, schema

## Usage

### Basic Analysis

Analyze the graph builder code with sample filings:

```bash
python -m src.cli analyze --year 2010 --limit 5
```

This will:
- Load the `graph_builder.py` code
- Analyze 5 sample filings from 2010
- Provide comprehensive analysis of parsing logic
- Suggest improvements
- **Save results** to `data/analysis/parsing_logic_YYYYMMDD_HHMMSS.json` and `.md`

### Pattern Analysis

Get suggestions for improved regex patterns:

```bash
python -m src.cli analyze --year 2010 --limit 5 --patterns
```

The AI will:
- Review current regex patterns
- Analyze filing content
- Suggest better patterns for extracting people, titles, relationships

### Missing Entities Analysis

Find entities that should have been extracted but weren't:

```bash
python -m src.cli analyze --year 2010 --limit 5 --missing
```

This will:
- Extract entities using current logic
- Compare with what's actually in the filing
- Identify missing people, companies, events, relationships

### Schema Suggestions

Get recommendations for improving the graph schema:

```bash
python -m src.cli analyze --year 2010 --limit 5 --schema
```

The AI will suggest:
- New node types or properties
- New relationship types
- Better indexing strategies
- Data structure optimizations

### Combined Analysis

Run all analyses at once:

```bash
python -m src.cli analyze --year 2010 --limit 5 --patterns --missing --schema
```

### List Previous Analyses

View all saved analysis results:

```bash
python -m src.cli analyze --list
```

This shows:
- All analysis types (parsing_logic, patterns, missing_entities, schema)
- Timestamps for each analysis
- Metadata (year, limit, etc.)
- Filenames for viewing

### View Specific Analysis

View a saved analysis result:

```bash
python -m src.cli analyze --view parsing_logic_20240115_143022.json
```

Or view the markdown version directly:
```bash
cat data/analysis/parsing_logic_20240115_143022.md
```

## How It Works

1. **Code Reading**: The analyzer reads your `graph_builder.py` source code
2. **Data Sampling**: Loads sample filings from your data directory
3. **AI Analysis**: Uses LLM to:
   - Understand current parsing logic
   - Compare with actual filing content
   - Identify gaps and improvements
4. **Suggestions**: Provides actionable recommendations with examples

## Storage Location

Analysis results are stored in:
```
data/analysis/
├── parsing_logic_20240115_143022.json
├── parsing_logic_20240115_143022.md
├── patterns_20240115_143045.json
├── patterns_20240115_143045.md
├── missing_entities_20240115_143100.json
└── missing_entities_20240115_143100.md
```

Each analysis includes:
- **Timestamp**: When the analysis was run
- **Metadata**: Year, limit, filings analyzed, etc.
- **Results**: Full AI analysis output

## Example Output

```
============================================================
AI-Powered Graph Builder Analysis
============================================================

Initializing AI analyzer...
✅ AI analyzer ready

Reading graph builder code...
✅ Loaded 25000 characters of code

Loading sample filings (limit: 5)...
  ✅ Loaded: filing1.txt
  ✅ Loaded: filing2.txt
  ✅ Loaded: filing3.txt
  ✅ Loaded: filing4.txt
  ✅ Loaded: filing5.txt
✅ Loaded 5 sample filings

============================================================
Running AI Analysis...
============================================================

📊 Analyzing parsing logic...
💾 Analysis saved to: data/analysis/parsing_logic_20240115_143022.json

============================================================
ANALYSIS RESULTS
============================================================

**Current Logic Analysis:**
- Good regex patterns for signature extraction
- Effective company node creation with proper CIK formatting
- Solid event type detection

**Issues Found:**
- Pattern for director extraction may miss titles in parentheses
- No handling for middle initials in names
- Missing extraction for board member relationships

**Suggestions:**
1. Improve name pattern to handle middle initials:
   r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'
   
2. Add pattern for board members:
   r'Board\s+of\s+Directors[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)'
   
3. Extract email addresses for contacts:
   r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'

...
```

## Integration with Development Workflow

1. **After parsing changes**: Run analysis to validate improvements
2. **Before major refactoring**: Get AI suggestions first
3. **Regular reviews**: Periodically analyze to catch missed patterns
4. **Schema evolution**: Use schema suggestions when adding new features
5. **Track progress**: Compare saved analyses over time to see improvements
6. **Share insights**: Markdown files can be shared with the team or added to git

## Tracking Analysis History

All analyses are saved with timestamps, so you can:
- **Compare over time**: See how suggestions change as code improves
- **Review past insights**: Revisit old analyses when making new changes
- **Track improvements**: Measure if suggested changes were implemented
- **Document decisions**: Keep a record of why certain patterns were chosen

## Configuration

The analyzer uses the same Ollama configuration as other AI features:

- **Model**: `llama3.2` (default)
- **Base URL**: `http://localhost:11434` (or `OLLAMA_BASE_URL` env var)
- **Context Window**: 4096 tokens (for code analysis)

## Limitations

- Analysis is based on sample filings (not all filings)
- Suggestions are recommendations, not guaranteed fixes
- LLM responses may vary between runs
- Requires Ollama to be running locally

## Troubleshooting

**"AI analyzer not available"**
- Check Ollama is running: `ollama list`
- Pull the model: `ollama pull llama3.2`

**"No filings found"**
- Ensure filings exist in `data/filings/YYYY/`
- Check the year parameter matches your data

**Slow analysis**
- Reduce `--limit` to analyze fewer filings
- Use a faster model (if available)

## Next Steps

After getting AI suggestions:
1. Review recommendations carefully
2. Test suggested patterns on sample data
3. Implement improvements incrementally
4. Re-run analysis to validate changes

