# AI-Based Relationship Extraction

## Overview

The Orion project now supports AI-based extraction of person-company relationships (`WORKS_AT`) from EDGAR filings using Ollama LLM. This provides more accurate relationship extraction compared to pattern-based regex matching.

## Prerequisites

1. **Ollama installed and running**
   - Download from: https://ollama.ai
   - Install a model: `ollama pull llama3.2` (or another model)

2. **Ollama service running**
   - Default: `http://localhost:11434`
   - Can be configured via `OLLAMA_BASE_URL` environment variable

## Configuration

### Environment Variables

- `OLLAMA_BASE_URL`: Base URL for Ollama API (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Model name to use (default: `llama3.2`)
- `USE_AI_EXTRACTION`: Enable/disable AI extraction (default: `true`)

### CLI Options

```bash
# Use AI extraction (default)
python -m src.cli load-graph --year 2009 --limit 10

# Disable AI extraction (use pattern-based)
python -m src.cli load-graph --year 2009 --limit 10 --no-ai
```

## How It Works

1. **AI Extraction (Primary)**: When enabled, the system:
   - Sends filing content to Ollama LLM
   - Uses a structured prompt to extract person-company relationships
   - Returns JSON with names, titles, and role types
   - Falls back to pattern-based extraction if AI fails

2. **Pattern-Based Extraction (Fallback)**: 
   - Uses regex patterns to find people and titles
   - Less accurate but doesn't require LLM
   - Automatically used if AI is unavailable

## Usage Example

```bash
# Set environment variables (optional)
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2"
export USE_AI_EXTRACTION="true"

# Load graph with AI extraction
python -m src.cli load-graph --year 2009 --limit 10
```

## Benefits

- **More Accurate**: AI understands context and can extract relationships that regex patterns miss
- **Better Title Extraction**: Correctly identifies job titles even when formatting varies
- **Context Awareness**: Understands which company a person works for based on document context
- **Automatic Fallback**: Seamlessly falls back to pattern-based extraction if AI is unavailable

## Troubleshooting

### "Warning: AI extraction requested but Ollama is not available"

- Ensure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Verify the base URL is correct

### "Could not initialize Ollama LLM"

- Check Ollama service is accessible at the configured URL
- Verify the model name is correct
- Check network connectivity

### Slow Processing

- AI extraction is slower than pattern-based extraction
- Consider using `--limit` for testing
- Use `--no-ai` for faster processing if accuracy is less critical

## Architecture

```
GraphBuilder
  ├── extract_people_from_filing() [Main entry point]
  │   ├── AI Extraction (if enabled)
  │   │   └── AIRelationshipExtractor.extract_relationships()
  │   │       └── Ollama LLM → JSON response
  │   └── Pattern-Based Extraction (fallback)
  │       └── _extract_people_from_filing_patterns()
  │           └── Regex pattern matching
```

## Future Enhancements

- Support for other LLM providers (OpenAI, Anthropic, etc.)
- Batch processing for multiple filings
- Caching of AI extraction results
- Fine-tuning prompts for better accuracy

