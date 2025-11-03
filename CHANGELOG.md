# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-03

### Added

- Initial release of Code Indexer
- Tree-sitter based code parsing for multiple languages
- Azure OpenAI embeddings integration for semantic search
- SQLite-based caching system with hash-based invalidation
- CLI interface with commands:
  - `index` - Index codebase with optional embeddings
  - `search` - Semantic code search
  - `map` - Generate codebase maps
  - `stats` - View cache statistics
  - `clear` - Clear cache
- Multi-language support:
  - Python
  - JavaScript
  - TypeScript
  - Go
  - Rust
  - Java
  - C++
  - C
  - C#
  - Ruby
- PowerShell automation script (`smart-code.ps1`) for Aider integration
- Comprehensive documentation:
  - Quick start guide
  - Usage guide with integration patterns
  - Real-world examples
  - Architecture documentation
  - Technical deep-dives (embedding flow, caching strategy)
- Test data and validation results
- MIT License

### Features

- 🚀 **Fast parsing**: Tree-sitter extracts signatures only (96% token reduction)
- 🤖 **Semantic search**: Natural language queries using Azure OpenAI embeddings
- 💾 **Smart caching**: Hash-based file tracking avoids re-parsing
- 🔍 **High accuracy**: 74-83% similarity scores for relevant results
- ⚡ **Performance**: 
  - Index 500 files in ~4 seconds
  - Generate 100 embeddings in ~10 seconds
  - Search in < 2 seconds
- 🌍 **Multi-language**: 11+ programming languages supported
- 📊 **Token efficiency**: 1.2M tokens → 48K tokens (96% reduction)
- 🗺️ **Code maps**: Human-readable codebase overviews

### Documentation

- `README.md` - Main project documentation
- `QUICKSTART.md` - 5-minute setup guide
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy and best practices
- `PUBLISHING.md` - GitHub publishing checklist
- `docs/USAGE-GUIDE.md` - Integration with AI coding assistants
- `docs/EXAMPLES.md` - Practical usage examples
- `docs/SMART-CODE-EXAMPLES.md` - Advanced workflow examples
- `docs/EMBEDDING-FLOW.md` - Technical architecture details
- `docs/PROJECT-SUMMARY.md` - Complete project overview
- `docs/TEST-RESULTS.md` - Validation and test results
- `docs/DEMO-RESULTS.md` - Complete workflow demonstration

### Technical Details

- Python 3.8+ required
- Dependencies:
  - `tree-sitter` 0.25.2
  - `openai` 2.6.1
  - `click` 8.3.0
  - `numpy` 2.3.4
  - `scipy` 1.16.3
  - Language parsers for all supported languages
- Cache format: SQLite database
- Embedding model: text-embedding-ada-002 (1536 dimensions)
- Storage: ~13.8 KB per embedding
- Architecture: Modular design (indexer, embeddings, cache, CLI)

---
