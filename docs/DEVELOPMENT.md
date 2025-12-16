# Development Guide

## Development Environment Setup

### Prerequisites
- Conda (Miniconda or Anaconda)
- Git
- Code editor (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd orion
   ```

2. **Create conda environment**
   ```bash
   ./setup_conda.sh
   conda activate orion
   ```

3. **Verify setup**
   ```bash
   python -m src.cli --help
   ```

## Development Workflow

### Running the Application

```bash
# Activate environment
conda activate orion

# Run CLI commands
python -m src.cli download --start-year 2009 --end-year 2010
python -m src.cli setup-db
python -m src.cli test-db --neo4j
```

### Code Structure

```
src/
├── cli.py              # CLI entry point
├── database/           # Database connections
├── data_loader.py      # Loads downloaded filings
├── graph_builder.py    # Builds Neo4j graph
├── services/           # Business logic (TODO)
└── models/             # Data models (TODO)
```

### Adding New Features

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature**
   - Follow existing code style
   - Add docstrings to functions/classes
   - Update documentation

3. **Test your changes**
   ```bash
   python -m src.cli test --download
   ```

4. **Update documentation**
   - Add to relevant docs in `docs/`
   - Update README if needed

5. **Commit and push**
   ```bash
   git add .
   git commit -m "Add feature: description"
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all functions/classes
- Keep functions focused and small

### Documentation
- Update relevant docs in `docs/`
- Add docstrings to code
- Update README for major changes

### Testing
- Test new features before committing
- Use the test command: `python -m src.cli test`
- Verify CLI commands work correctly

## Common Tasks

### Adding a New CLI Command

1. **Add command to `src/cli.py`**
   ```python
   def your_command(args):
       """Handle your command."""
       # Implementation
   
   # In main():
   your_parser = subparsers.add_parser("your-command", ...)
   your_parser.set_defaults(func=your_command)
   ```

2. **Test the command**
   ```bash
   python -m src.cli your-command --help
   ```

### Adding Database Operations

1. **Add methods to connection classes**
   - `src/database/neo4j_connection.py`
   - `src/database/oracle_connection.py`

2. **Test connections**
   ```bash
   python -m src.cli test-db --neo4j
   ```

### Adding New Dependencies

1. **Update `environment.yml`**
   ```yaml
   dependencies:
     - pip:
         - your-package>=1.0.0
   ```

2. **Update environment**
   ```bash
   conda env update -f environment.yml --prune
   ```

## Debugging

### Check Python Environment
```bash
which python
python --version
python -c "import sys; print(sys.executable)"
```

### Check Conda Environment
```bash
conda info --envs
conda activate orion
conda list
```

### Test Database Connections
```bash
python -m src.cli test-db --neo4j
python -m src.cli test-db --oracle
```

### View Logs
- Check console output for errors
- Check `.env` file for configuration
- Verify database credentials

## Troubleshooting

### Environment Issues
- **Problem**: Wrong Python version
  - **Solution**: `conda activate orion` and verify with `which python`

### Database Issues
- **Problem**: Connection failed
  - **Solution**: Check `.env` file and database credentials
  - **Solution**: Verify database is running

### Import Errors
- **Problem**: Module not found
  - **Solution**: `conda env update -f environment.yml --prune`
  - **Solution**: Verify you're in the orion environment

## Project Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Conda setup
- [x] Database connections
- [x] SEC ingestion
- [x] CLI interface

### Phase 2: Core Functionality (In Progress)
- [ ] Document processing
- [ ] LLM integration
- [ ] Graph creation
- [ ] Vector storage

### Phase 3: Advanced Features
- [ ] Semantic search
- [ ] Relationship discovery
- [ ] API endpoints
- [ ] Web interface

## Contributing

1. Follow the development workflow
2. Write clear commit messages
3. Update documentation
4. Test your changes
5. Submit pull requests

## Resources

- [Installation Guide](INSTALLATION.md)
- [CLI Usage](CLI_USAGE.md)
- [Architecture](ARCHITECTURE.md)
- [Neo4j Schema](neo4j_schema.md)

