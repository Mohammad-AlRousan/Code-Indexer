# Code-Indexer + Aider Integration Guide

Complete guide for integrating semantic code search with Aider for smarter AI-assisted coding.

## Why Integrate?

| **Aider Alone** | **Aider + Code-Indexer** |
|-----------------|--------------------------|
| LLM sees only added files | LLM gets semantic context from entire codebase |
| Manual file selection | Auto-discover relevant files |
| Limited to token budget | Full codebase indexed offline |
| Dependency-graph ranking | Semantic similarity matching |
| Session-scoped context | Persistent searchable knowledge base |

**Result**: Aider makes better decisions with richer, more relevant context.

---

## Integration Methods

### 1️⃣ **Aider Plugin** (Recommended for Daily Use)

**Best for**: Interactive coding sessions with semantic file discovery

**Setup**:
```powershell
# Copy plugin
cp aider_plugin/code_index_commands.py ~/.aider/plugins/

# Or configure in .aider.conf.yml
plugins:
  - path: C:/code/Code-Indexer/aider_plugin/code_index_commands.py
```

**Usage in Aider**:
```bash
# Search and add relevant files
/index-search "authentication middleware"

# Load full codebase map
/index-map src/

# Refresh index after changes
/index-refresh
```

**Workflow Example**:
```bash
$ aider

# Start with search
> /index-search "database connection setup"
Found 5 results
Add src/db/connection.py? [y/n]: y
Add src/db/pool.py? [y/n]: y

# Now ask Aider to make changes
> "Add connection retry logic similar to existing patterns"

# Aider now has context from semantically similar code!
```

---

### 2️⃣ **Smart Wrapper Script** (Best for Automation)

**Best for**: Scripted workflows, CI/CD, automated refactoring

**Setup**:
```powershell
# Make script available
$env:PATH += ";C:\code\Code-Indexer\scripts"
```

**Usage**:
```powershell
# Quick task with auto-context
.\scripts\aider-smart.ps1 `
  -Task "Add rate limiting to API endpoints" `
  -SearchQuery "rate limit throttle" `
  -AutoAddFiles `
  -GenerateMap

# Discover files interactively
.\scripts\aider-smart.ps1 `
  -SearchQuery "error handling retry" `
  -TopK 10

# Explicit files + semantic discovery
.\scripts\aider-smart.ps1 `
  -Files src/api/auth.py `
  -SearchQuery "authentication pattern" `
  -Directory src/
```

**Benefits**:
- ✅ Auto-indexes before each session
- ✅ Discovers relevant files semantically
- ✅ Generates codebase map for context
- ✅ Combines Aider's repo map with Code-Indexer's semantic search

---

### 3️⃣ **API Server** (Best for Multi-Tool Integration)

**Best for**: VS Code extensions, web UIs, multiple clients

**Setup**:
```powershell
# Start API server
python src/api_server.py --port 8080

# In separate terminal, use Aider with API plugin
aider --plugins aider_plugin/api_integration.py
```

**API Endpoints**:
```python
# Search semantically
POST http://localhost:8080/search
{
  "query": "authentication functions",
  "top_k": 10,
  "threshold": 0.7
}

# Index directory
POST http://localhost:8080/index
{
  "directory": "src/",
  "with_embeddings": true
}

# Get codebase map
GET http://localhost:8080/map?directory=src/

# Cache stats
GET http://localhost:8080/stats
```

**Usage in Aider**:
```bash
$ aider --plugins aider_plugin/api_integration.py

> /api-search "HTTP client retry logic"
Found 5 results...

> /api-index --directory src/
✅ Indexed 156 files, 1,234 definitions

> /api-stats
Cached files: 156
Total embeddings: 1,234
```

**Benefits**:
- ✅ Centralized index service
- ✅ Multiple clients can use same index
- ✅ Real-time updates across tools
- ✅ RESTful API for custom integrations

---

### 4️⃣ **VS Code Extension** (Best for GUI Users)

**Best for**: Visual Studio Code users who prefer GUI

**Setup**:
```powershell
cd vscode-extension
npm install
npm run compile

# Install in VS Code
code --install-extension .
```

**Features**:
- 🔍 **Semantic Search Panel**: Search from sidebar
- 📁 **Aider Context Manager**: Track files added to context
- ⌨️ **Keyboard Shortcuts**:
  - `Ctrl+Shift+F`: Semantic search
  - `Ctrl+Shift+A`: Smart Aider session
- 🔄 **Auto-Index**: Refreshes on workspace open

**Workflow**:
1. Press `Ctrl+Shift+A` (Smart Aider)
2. Enter task: "Add authentication to API"
3. Enter search query: "auth middleware"
4. Extension auto-discovers relevant files
5. Opens Aider terminal with full context

---

### 5️⃣ **Git Hook** (Best for Always-Fresh Index)

**Best for**: Ensuring index is never stale

**Setup**:
```powershell
# Install pre-commit hook
cp hooks/pre-commit .git/hooks/
```

**Behavior**:
- Auto-updates index when committing code files
- Runs in background (non-blocking)
- Keeps cache fresh for Aider sessions

**Combined with Aider**:
```bash
# Make changes
$ git add .

# Pre-commit hook runs
🔄 Updating code index...
✅ Index updated

# Commit
$ git commit -m "Add feature"

# Now Aider has latest context
$ aider
> /index-search "new feature"  # Immediately finds your changes!
```

---

## Best Practices

### 🎯 **Optimal Workflow**

```powershell
# 1. Index your project (once)
python src/cli.py index . --with-embeddings

# 2. Use smart wrapper for tasks
.\scripts\aider-smart.ps1 `
  -Task "Refactor authentication module" `
  -SearchQuery "auth login session" `
  -AutoAddFiles `
  -GenerateMap

# 3. Aider now has:
#    ✅ Semantically relevant files auto-added
#    ✅ Full codebase map for context
#    ✅ Aider's own repo map (1k tokens)
#    ✅ Code-Indexer's semantic context (unlimited)
```

### 📊 **When to Use Each Method**

| Method | Use Case |
|--------|----------|
| **Plugin** | Daily coding, interactive discovery |
| **Wrapper Script** | Automated tasks, CI/CD, batch operations |
| **API Server** | Multi-tool integration, team sharing |
| **VS Code Extension** | GUI users, visual workflow |
| **Git Hook** | Keep index fresh automatically |

### 🚀 **Power User Combo**

```yaml
# .aider.conf.yml
plugins:
  - path: C:/code/Code-Indexer/aider_plugin/code_index_commands.py

# Auto-refresh index on start
startup:
  - python C:/code/Code-Indexer/src/cli.py index . --with-embeddings

# Always load codebase map
read:
  - .aider-context.txt

# Generate map on startup
before-session:
  - python C:/code/Code-Indexer/src/cli.py map . --output .aider-context.txt

# Combine with Aider's repo map
map-tokens: 2000
```

**Result**: Every Aider session has BOTH:
1. **Aider's optimized repo map** (1-2k tokens, dependency-ranked)
2. **Code-Indexer's semantic index** (full codebase, similarity-ranked)

---

## Comparison: Aider Repo Map vs Code-Indexer

### **Complementary Strengths**

| Feature | Aider Repo Map | Code-Indexer |
|---------|---------------|--------------|
| **Goal** | LLM context optimization | Semantic code discovery |
| **Scope** | Token-budget limited (~1-2k) | Full codebase indexed |
| **Ranking** | Dependency graph | Semantic similarity |
| **Search** | Implicit (chat context) | Explicit (natural language) |
| **Update** | Per-session dynamic | Persistent cache |
| **Query** | None (auto-selected) | "Find auth functions" |
| **Storage** | In-memory | SQLite + embeddings |
| **Use Case** | Give LLM smart context | Find relevant files first |

### **How They Work Together**

```
1. User asks: "Add rate limiting to API"
   ↓
2. Code-Indexer searches: "rate limit throttle middleware"
   → Finds: rate_limiter.py, throttle.py, middleware.py
   ↓
3. Add these to Aider chat
   ↓
4. Aider's repo map analyzes dependencies
   → Includes: config.py (imported by rate_limiter)
   → Includes: decorators.py (dependency of middleware)
   ↓
5. LLM now has:
   - Semantically relevant files (Code-Indexer)
   - Dependency context (Aider repo map)
   - Full codebase overview (Code-Indexer map)
   ↓
6. RESULT: Best possible context for the task! 🎯
```

---

## Real-World Examples

### **Example 1: Feature Addition**

```powershell
# Task: Add OAuth2 authentication
.\scripts\aider-smart.ps1 `
  -Task "Implement OAuth2 authentication flow" `
  -SearchQuery "authentication oauth login" `
  -AutoAddFiles

# Code-Indexer finds:
# - existing_auth.py (similar auth patterns)
# - session_manager.py (session handling)
# - token_validator.py (token logic)

# Aider uses these as context to implement OAuth2
# following existing patterns!
```

### **Example 2: Bug Investigation**

```bash
$ aider

# Search for error handling patterns
> /index-search "error handling exception retry"

# Add relevant files
> y, y, n, y

# Ask Aider to analyze
> "Why are some error handlers missing retry logic?"

# Aider can now compare ALL error handlers!
```

### **Example 3: Refactoring**

```powershell
# Find all duplicate logic
python src/cli.py search "database connection setup" --top-k 20

# Review results, identify patterns

# Use Aider to consolidate
.\scripts\aider-smart.ps1 `
  -Task "Consolidate DB connection logic into single module" `
  -Files (results from search)
```

---

## Troubleshooting

### **Plugin not loading**

```bash
# Check Aider config
cat .aider.conf.yml

# Verify plugin path exists
ls C:/code/Code-Indexer/aider_plugin/code_index_commands.py
```

### **API server not responding**

```powershell
# Check server status
curl http://localhost:8080/health

# Restart server
python src/api_server.py --port 8080
```

### **Search returns no results**

```powershell
# Verify embeddings exist
python src/cli.py stats

# Re-index with embeddings
python src/cli.py index . --with-embeddings --force
```

---

## Performance Tips

1. **Index incrementally**: Use git hook to keep cache fresh
2. **Narrow searches**: Use `--file-pattern` and `--type` filters
3. **Adjust threshold**: Lower for broader results, higher for precision
4. **Cache reuse**: Multiple projects can share cache with `--cache-dir`

---

## Next Steps

1. ✅ Install preferred integration method (plugin recommended)
2. ✅ Index your codebase: `python src/cli.py index .`
3. ✅ Try smart wrapper: `.\scripts\aider-smart.ps1`
4. ✅ Configure `.aider.conf.yml` for auto-context
5. ✅ Enable git hook for auto-updates

**Ready to code smarter? Start with the plugin!** 🚀
