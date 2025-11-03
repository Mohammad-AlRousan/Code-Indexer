# Usage Examples

Real-world examples of using Code Indexer.

## Example 1: Index a Python Project

```powershell
# Setup
cd c:\code\aider\code-indexer
.\.venv\Scripts\Activate.ps1

# Index a Django project
python src\cli.py index C:\code\my-django-app --with-embeddings

# Results:
# ✅ Indexed 87 files, 456 definitions
# 💾 Cache size: 1.2 MB
```

## Example 2: Find Authentication Functions

```powershell
# Search
python src\cli.py search "authentication login function"

# Results:
# 1. authenticate_user (function) - 0.921
#    📁 src/auth/views.py
#    📝 def authenticate_user(username: str, password: str) -> Optional[User]:
#
# 2. login_required (decorator) - 0.887
#    📁 src/auth/decorators.py
#    📝 def login_required(view_func):
#
# 3. process_login (function) - 0.856
#    📁 src/auth/handlers.py
#    📝 async def process_login(request: Request) -> Response:
```

## Example 3: Index Multiple Projects

```powershell
# Index several projects
python src\cli.py index C:\code\frontend --cache-dir .cache\frontend
python src\cli.py index C:\code\backend --cache-dir .cache\backend
python src\cli.py index C:\code\shared --cache-dir .cache\shared

# Each project gets its own cache
```

## Example 4: Filter by File Type

```powershell
# Only search TypeScript files
python src\cli.py search "React component" --file-pattern "*.tsx"

# Only search test files
python src\cli.py search "mock data" --file-pattern "*test.py"
```

## Example 5: Generate Documentation Map

```powershell
# Generate map for documentation
python src\cli.py map C:\code\my-project --output docs\API_REFERENCE.txt

# Map shows:
# - All classes and their methods
# - All functions with signatures
# - File organization
```

Example output:
```
===== CODEBASE MAP =====

FILE: src/api/users.py (python)
  class UserAPI:
    def __init__(self, db: Database):
    async def get_user(self, user_id: int) -> User:
    async def create_user(self, data: UserCreate) -> User:
    async def update_user(self, user_id: int, data: UserUpdate) -> User:
    async def delete_user(self, user_id: int) -> None:

FILE: src/api/posts.py (python)
  class PostAPI:
    def __init__(self, db: Database):
    async def list_posts(self, limit: int = 100) -> List[Post]:
    async def get_post(self, post_id: int) -> Post:
```

## Example 6: Track Cache Growth

```powershell
# Check stats before
python src\cli.py stats

# Index new files
python src\cli.py index . --force

# Check stats after
python src\cli.py stats
```

## Example 7: Search with Filters

```powershell
# Find only class methods about database
python src\cli.py search "database query" --type method --threshold 0.8

# Find async functions
python src\cli.py search "async" --type function --top-k 20

# High-precision search (higher threshold)
python src\cli.py search "email validation" --threshold 0.9
```

## Example 8: Incremental Indexing

```powershell
# First index
python src\cli.py index .

# Edit files...
# (code changes)

# Re-index (only changed files processed)
python src\cli.py index .

# Results:
# 📁 Scanning files...
# ✅ Indexed 156 files, 1,234 definitions
# (Note: Unchanged files skipped via hash check)
```

## Example 9: Use as Python Library

```python
from pathlib import Path
from src.indexer import TreeSitterIndexer
from src.embeddings import AzureEmbeddingsService
from src.cache import IndexCache

# Initialize
indexer = TreeSitterIndexer()
cache = IndexCache('.my_cache')

# Index a single file
result = indexer.index_file('example.py')
print(f"Found {len(result['definitions'])} definitions")

# Cache it
cache.save_file_index('example.py', result['file_hash'], result)

# Generate embeddings
embeddings_service = AzureEmbeddingsService(
    endpoint='https://your-resource.openai.azure.com',
    api_key='your-key'
)

embedded = embeddings_service.embed_index(result)

# Save embeddings
cache.save_embeddings('example.py', embedded['example.py']['definitions'])

# Search
query = "function that validates input"
query_embedding = embeddings_service.generate_embedding(query)

all_defs = embedded['example.py']['definitions']
similar = embeddings_service.find_similar_definitions(
    query_embedding,
    all_defs,
    top_k=5,
    threshold=0.7
)

for match in similar:
    print(f"{match['name']}: {match['similarity']:.3f}")
    print(f"  {match['signature']}")
```

## Example 10: Batch Processing

```python
from src.indexer import TreeSitterIndexer
from src.embeddings import AzureEmbeddingsService

indexer = TreeSitterIndexer()
embeddings_service = AzureEmbeddingsService(
    endpoint='https://your-resource.openai.azure.com',
    api_key='your-key'
)

# Index multiple directories
projects = [
    'C:\\code\\project1',
    'C:\\code\\project2',
    'C:\\code\\project3'
]

for project in projects:
    print(f"Indexing {project}...")
    
    # Index
    result = indexer.index_directory(project)
    
    # Embed
    embedded = embeddings_service.embed_index(result)
    
    # Process results
    total_defs = sum(
        len(file_data.get('definitions', []))
        for file_data in embedded.values()
    )
    
    print(f"  {len(embedded)} files, {total_defs} definitions")
```

## Example 11: Custom Ignore Patterns

```powershell
# Ignore tests and generated files
python src\cli.py index . `
  -i "test_*.py" `
  -i "*.spec.ts" `
  -i "generated/**" `
  -i "migrations/**"

# Or use environment variable
# In .env:
# CODE_INDEXER_IGNORE_PATTERNS=test_*,*.spec.ts,generated/**,migrations/**

python src\cli.py index .
```

## Example 12: Clear and Rebuild Cache

```powershell
# Clear cache
python src\cli.py clear

# Rebuild from scratch
python src\cli.py index . --with-embeddings --force
```

## Example 13: Search Across Languages

```powershell
# Index polyglot project (Python + TypeScript)
python src\cli.py index .

# Search finds matches in both languages
python src\cli.py search "HTTP request handler"

# Results:
# 1. handle_request (function) - 0.913
#    📁 src/api/handlers.py
#    📝 async def handle_request(request: Request) -> Response:
#
# 2. handleRequest (function) - 0.898
#    📁 frontend/src/api.ts
#    📝 async function handleRequest(req: Request): Promise<Response>
```

## Example 14: Compare Similar Code

```powershell
# Find all similar implementations
python src\cli.py search "calculate total price" --top-k 10 --threshold 0.6

# Review results to find duplicate logic
# Refactor to DRY principle
```

## Example 15: Integration with Aider

```powershell
# Index your codebase
python c:\code\aider\code-indexer\src\cli.py index .

# Generate map for context
python c:\code\aider\code-indexer\src\cli.py map . --output codebase-map.txt

# Use with Aider
wsl aider --model azure/gpt-4o-realtime `
  --map-tokens 1000 `
  --read codebase-map.txt
```

## Tips and Tricks

### Faster Embeddings

```powershell
# Process files in batches (already done automatically)
# The embeddings service batches up to 16 texts per API call
```

### Monitoring Performance

```python
import time
from src.indexer import TreeSitterIndexer

indexer = TreeSitterIndexer()

start = time.time()
result = indexer.index_directory('.')
elapsed = time.time() - start

print(f"Indexed in {elapsed:.2f}s")
print(f"Files/sec: {len(result) / elapsed:.1f}")
```

### Custom Similarity Threshold

```powershell
# High precision (fewer, more relevant results)
python src\cli.py search "validation" --threshold 0.9

# High recall (more results, may be less relevant)
python src\cli.py search "validation" --threshold 0.5
```

### Combining with Git

```bash
# Index only tracked files
git ls-files | ForEach-Object { python src\cli.py index $_ }

# Index files changed in last commit
git diff --name-only HEAD~1 | ForEach-Object {
    python src\cli.py index $_ --force
}
```

---

For more examples, see:
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
