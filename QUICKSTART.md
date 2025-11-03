# Quick Start Guide

Get started with Code Indexer in 5 minutes!

## 1. Setup (One-time)

```powershell
# Navigate to project
cd c:\code\aider\code-indexer

# Run setup script
.\setup.ps1

# Edit .env with your Azure OpenAI credentials
notepad .env
```

## 2. Configure Azure OpenAI

Edit `.env`:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

Get credentials from [Azure Portal](https://portal.azure.com) → Azure OpenAI → Keys and Endpoint

## 3. Index Your First Project

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Index a directory
python src\cli.py index C:\code\my-project

# This will:
# - Parse all code files with Tree-sitter
# - Extract function/class signatures
# - Generate Azure OpenAI embeddings
# - Cache everything in SQLite
```

Expected output:
```
🔍 Indexing C:\code\my-project...
📁 Scanning files...
✅ Indexed 156 files, 1,234 definitions
💾 Saving to cache...
🤖 Generating embeddings with Azure OpenAI...
Embedding files: [####################] 156/156
✅ Embeddings generated and cached

📊 Cache stats:
   Files: 156
   Definitions: 1,234
   Embeddings: 1,234
   Cache size: 2.45 MB
```

## 4. Search Your Code

```powershell
# Natural language search
python src\cli.py search "function that validates email addresses"

# Search with filters
python src\cli.py search "HTTP handler" --type function --top-k 5
```

Output:
```
🔎 Searching for: function that validates email addresses
🤖 Generating query embedding...
🔍 Searching cache...

✅ Found 3 results:

1. validate_email (function) - 0.912
   📁 src/utils/validation.py
   📝 def validate_email(email: str) -> bool:

2. is_valid_email (function) - 0.854
   📁 src/auth/validators.py
   📝 def is_valid_email(address: str) -> bool:
```

## 5. Generate Codebase Map

```powershell
# View code structure
python src\cli.py map C:\code\my-project
```

## Common Commands

| Command | Description | Example |
|---------|-------------|---------|
| `index` | Index a directory | `python src\cli.py index .` |
| `search` | Search semantically | `python src\cli.py search "error handling"` |
| `map` | Generate codebase map | `python src\cli.py map .` |
| `stats` | View cache stats | `python src\cli.py stats` |
| `clear` | Clear cache | `python src\cli.py clear` |

## Tips

1. **Re-indexing is fast** - Unchanged files are skipped (hash-based caching)
2. **Use specific queries** - "function that parses JSON files" works better than "JSON"
3. **Filter results** - Use `--type`, `--file-pattern`, `--threshold` for better results
4. **Save maps** - `python src\cli.py map . --output docs\codebase.txt`

## Troubleshooting

### "AZURE_OPENAI_ENDPOINT not set"

→ Create `.env` file with your credentials (see step 2)

### "No embeddings in cache"

→ Run `python src\cli.py index . --with-embeddings`

### Slow indexing

→ Normal for first run. Subsequent runs use cache and are much faster.

### Need help?

→ Run `python src\cli.py --help` or see [README.md](README.md)

## Next Steps

- Read [full documentation](README.md)
- Explore [Azure OpenAI embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/understand-embeddings)

---

**Ready to index?**

```powershell
.\.venv\Scripts\Activate.ps1
python src\cli.py index . --with-embeddings
```
