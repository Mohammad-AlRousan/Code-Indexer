# Contributing to Code Indexer

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)

### Suggesting Features

We welcome feature suggestions! Please:
- Check existing issues first
- Describe the use case
- Explain the expected behavior
- Consider implementation details

### Pull Requests

1. **Fork the repository**
2. **Create a branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
4. **Test your changes**
   ```bash
   python src/cli.py index test_data
   python src/cli.py search "test query"
   ```
5. **Commit** (`git commit -m 'Add amazing feature'`)
6. **Push** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/Mohammad-AlRousan
Code-Indexer.git
cd code-indexer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install tree-sitter languages
python -c "from tree_sitter_languages import get_parser; get_parser('python')"

# Set up environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions focused and testable

## Testing

Before submitting:

```bash
# Test indexing
python src/cli.py index test_data

# Test search
python src/cli.py search "function" --top-k 5

# Test map generation
python src/cli.py map test_data --output test-map.txt

# Check stats
python src/cli.py stats
```

## Adding Language Support

To add a new language:

1. Add tree-sitter parser to `requirements.txt`
2. Update `LANGUAGE_PARSERS` in `src/indexer.py`
3. Add query patterns for the language
4. Test with sample files
5. Update documentation

## Questions?

Feel free to open an issue for questions or join discussions!

## Code of Conduct

Be respectful, inclusive, and constructive. We're here to build great tools together!
