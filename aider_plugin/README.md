# 🔗 Aider + Code-Indexer Integration

This directory contains integration tools to combine **Code-Indexer's semantic search** with **Aider's AI coding assistant**.

## 📦 What's Included

### Plugins
- **`code_index_commands.py`** - Aider plugin with `/index-search`, `/index-map`, `/index-refresh` commands
- **`api_integration.py`** - API client plugin for server-based integration
- **`README.md`** - Plugin setup and usage guide

## 🚀 Quick Start

### Option 1: Load Plugin in Aider Config

Create `.aider.conf.yml` in your project:

```yaml
plugins:
  - path: C:/code/Code-Indexer/aider_plugin/code_index_commands.py

# Auto-index on startup
startup:
  - python C:/code/Code-Indexer/src/cli.py index . --with-embeddings
```

### Option 2: Manual Plugin Load

```bash
$ aider --config .aider.conf.yml

# Or specify at runtime
$ aider --plugin C:/code/Code-Indexer/aider_plugin/code_index_commands.py
```

## 🎯 Available Commands

### `/index-search "query"`
Search codebase semantically and add relevant files to chat.

```bash
> /index-search "authentication middleware"

Found 5 results:
1. AuthMiddleware (class) - 0.912
   📁 src/middleware/auth.py
   📝 class AuthMiddleware:

Add src/middleware/auth.py to chat? [y/n]: y
✅ Added src/middleware/auth.py
```

### `/index-map [directory]`
Generate and load codebase map into context.

```bash
> /index-map src/

✅ Codebase map loaded into context
```

### `/index-refresh [--force]`
Re-index the codebase.

```bash
> /index-refresh

🔍 Indexing .
✅ Indexed 156 files, 1,234 definitions
✅ Index refreshed
```

## 💡 Example Workflow

```bash
# Start Aider
$ aider

# Search for relevant context
> /index-search "database connection pooling"

Found 3 results:
1. DatabasePool (class) - 0.945
2. create_connection_pool (function) - 0.887
3. PoolManager (class) - 0.821

# Add relevant files
Add src/db/pool.py? [y]: y
Add src/db/connection.py? [y]: y

# Now ask Aider to make changes
> "Add connection timeout configuration to the pool"

# Aider has full context from semantically similar code!
```

## 🔧 Advanced Configuration

### Auto-Context Workflow

```yaml
# .aider.conf.yml

plugins:
  - path: C:/code/Code-Indexer/aider_plugin/code_index_commands.py

# Refresh index before each session
before-session:
  - python C:/code/Code-Indexer/src/cli.py index . --with-embeddings

# Always load codebase map
read:
  - .aider-context.txt

# Generate map on startup
startup:
  - python C:/code/Code-Indexer/src/cli.py map . --output .aider-context.txt

# Combine with Aider's repo map
map-tokens: 2000
```

Now every Aider session has:
- ✅ Fresh semantic index
- ✅ Full codebase map loaded
- ✅ Aider's dependency-based repo map
- ✅ Combined context for best results!

## 📚 Full Documentation

See **[../docs/AIDER-INTEGRATION.md](../docs/AIDER-INTEGRATION.md)** for complete integration guide including:
- All 5 integration methods
- Performance optimization
- Troubleshooting
- Real-world examples

## 🤝 How It Complements Aider

| Feature | Aider Alone | + Code-Indexer |
|---------|-------------|----------------|
| File discovery | Manual | Semantic search |
| Context scope | Token-limited | Full codebase |
| Search method | Dependency graph | Vector similarity |
| Query type | Implicit | Natural language |
| Pattern finding | Limited | Semantic matching |

**Together = Best of both worlds!** 🎯

## 🐛 Troubleshooting

### Plugin not found
```bash
# Check path in config
cat .aider.conf.yml

# Verify file exists
ls C:/code/Code-Indexer/aider_plugin/code_index_commands.py
```

### Commands not working
```bash
# Check plugin loaded
> /help

# Should show:
# /index-search - Search codebase semantically
# /index-map - Generate and load codebase map
# /index-refresh - Re-index the codebase
```

### No search results
```powershell
# Verify embeddings exist
python C:/code/Code-Indexer/src/cli.py stats

# Re-index if needed
python C:/code/Code-Indexer/src/cli.py index . --with-embeddings --force
```

## 📖 Learn More

- [Main README](../README.md)
- [Integration Summary](../INTEGRATION-SUMMARY.md)
- [Full Integration Guide](../docs/AIDER-INTEGRATION.md)
- [Usage Examples](../docs/EXAMPLES.md)

---

**Ready to supercharge your Aider workflow?** Start with the Quick Start above! 🚀
