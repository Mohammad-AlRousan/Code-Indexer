# Using Code Indexer to Generate Better Code

The code indexer helps AI assistants understand your codebase better, leading to more accurate, context-aware code generation.

## Integration with Aider

### Workflow 1: Context-Aware Code Generation

**Step 1: Index your codebase**
```powershell
cd C:\code\your-project
python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings
```

**Step 2: Search for relevant code before implementing**
```powershell
# Before implementing authentication, find existing patterns
python C:\code\aider\code-indexer\src\cli.py search "authentication login function" --top-k 5

# Results show existing auth implementations:
# 1. authenticate_user (function) - 0.921
# 2. login_handler (function) - 0.887
# 3. verify_credentials (function) - 0.856
```

**Step 3: Generate codebase map for context**
```powershell
python C:\code\aider\code-indexer\src\cli.py map . --output codebase-map.txt
```

**Step 4: Use with Aider**
```powershell
# Pass the map to Aider for context
wsl aider --model azure/gpt-4o `
  --read codebase-map.txt `
  --message "Create a new authentication function following the existing patterns"
```

Aider now understands:
- Existing authentication patterns
- Naming conventions
- Code structure
- Dependencies used

### Workflow 2: Find Similar Code to Reuse

**Before writing new code, search for similar implementations:**

```powershell
# Task: Implement email validation
python C:\code\aider\code-indexer\src\cli.py search "validate email address" --top-k 3

# Results:
# 1. validate_email (function) - 0.912
#    📁 src/utils/validation.py
#    📝 def validate_email(email: str) -> bool:
```

**Action**: Review the existing implementation, reuse or extend it instead of duplicating.

### Workflow 3: Understand Code Before Modifying

**When asked to modify unfamiliar code:**

```powershell
# Search for related functionality
python C:\code\aider\code-indexer\src\cli.py search "database query user" --file-pattern "*.py"

# Generate focused map
python C:\code\aider\code-indexer\src\cli.py map src/database --output db-context.txt
```

**Use the context with Aider:**
```powershell
wsl aider src/database/users.py `
  --read db-context.txt `
  --message "Add pagination to user queries following existing patterns"
```

## Integration Patterns

### Pattern 1: Smart Context Selection

Instead of sending entire files to AI (wastes tokens), send signatures only:

**Traditional approach (wasteful):**
```powershell
# Sends entire file (10,000 tokens)
wsl aider --read src/services/user_service.py
```

**Better approach (efficient):**
```powershell
# Generate signature-only map (400 tokens - 96% savings!)
python C:\code\aider\code-indexer\src\cli.py map src/services --output context.txt
wsl aider --read context.txt
```

### Pattern 2: Pre-Implementation Research

**Before implementing ANY new feature:**

1. **Search for similar code**
   ```powershell
   python C:\code\aider\code-indexer\src\cli.py search "your feature description"
   ```

2. **Review existing patterns**
   - Check naming conventions
   - See how errors are handled
   - Understand existing architecture

3. **Generate focused context**
   ```powershell
   python C:\code\aider\code-indexer\src\cli.py map relevant-directory
   ```

4. **Code with context**
   ```powershell
   wsl aider --read context.txt --message "Implement new feature following existing patterns"
   ```

### Pattern 3: Refactoring Assistant

**Find duplicate or similar code to refactor:**

```powershell
# Find all similar implementations
python C:\code\aider\code-indexer\src\cli.py search "calculate total price" --top-k 10 --threshold 0.6

# Results show 5 similar implementations across different files
# → Time to refactor into shared utility!
```

**Then use Aider to refactor:**
```powershell
wsl aider file1.py file2.py file3.py `
  --message "Extract common price calculation logic into utils/pricing.py"
```

## Practical Examples

### Example 1: Adding API Endpoint

**Traditional approach:**
```powershell
# No context - AI might use wrong patterns
wsl aider --message "Add GET /api/users/{id} endpoint"
```

**Better approach:**
```powershell
# 1. Find existing API patterns
python C:\code\aider\code-indexer\src\cli.py search "API endpoint handler" --file-pattern "*/api/*"

# 2. Generate API module map
python C:\code\aider\code-indexer\src\cli.py map src/api --output api-context.txt

# 3. Code with full context
wsl aider src/api/users.py `
  --read api-context.txt `
  --message "Add GET /api/users/{id} endpoint following existing patterns"
```

**Result**: AI generates code matching your:
- Route registration pattern
- Error handling style
- Response format
- Authentication approach

### Example 2: Bug Fix with Context

**Scenario**: Fix a bug in payment processing

```powershell
# 1. Understand the payment module
python C:\code\aider\code-indexer\src\cli.py map src/payments --output payment-context.txt

# 2. Find related functions
python C:\code\aider\code-indexer\src\cli.py search "process payment transaction" --top-k 5

# 3. Fix with context
wsl aider src/payments/processor.py `
  --read payment-context.txt `
  --message "Fix the refund processing bug while maintaining compatibility with existing code"
```

**Benefit**: AI understands the full context and won't break related functionality.

### Example 3: Feature Development

**Task**: Add caching to database queries

```powershell
# 1. Search for existing caching
python C:\code\aider\code-indexer\src\cli.py search "cache redis memcache" --top-k 10

# Found existing Redis cache implementation!

# 2. Get cache module context
python C:\code\aider\code-indexer\src\cli.py map src/cache --output cache-context.txt

# 3. Extend existing pattern
wsl aider src/database/queries.py `
  --read cache-context.txt `
  --message "Add Redis caching to user queries using the existing cache service"
```

**Result**: Consistent caching implementation across the codebase.

## Creating a Code Generation Script

Save this as `smart-code.ps1`:

```powershell
# Smart Code Generation Helper
param(
    [Parameter(Mandatory=$true)]
    [string]$Task,
    
    [string]$SearchQuery = "",
    [string]$Directory = ".",
    [string[]]$Files = @()
)

$IndexerPath = "C:\code\aider\code-indexer"

Write-Host "🔍 Preparing context for: $Task" -ForegroundColor Cyan

# Search for similar code
if ($SearchQuery) {
    Write-Host "`n📊 Searching for similar code..." -ForegroundColor Yellow
    & "$IndexerPath\.venv\Scripts\python.exe" "$IndexerPath\src\cli.py" search "$SearchQuery" --top-k 5
}

# Generate context map
Write-Host "`n🗺️  Generating codebase map..." -ForegroundColor Yellow
& "$IndexerPath\.venv\Scripts\python.exe" "$IndexerPath\src\cli.py" map $Directory --output "temp-context.txt"

# Run Aider with context
Write-Host "`n🤖 Starting Aider with context..." -ForegroundColor Green
if ($Files.Count -gt 0) {
    wsl aider @Files --read temp-context.txt --message $Task
} else {
    wsl aider --read temp-context.txt --message $Task
}

# Cleanup
Remove-Item temp-context.txt -ErrorAction SilentlyContinue
```

**Usage:**
```powershell
# Example 1: Add new feature
.\smart-code.ps1 -Task "Add user authentication" -SearchQuery "authentication login" -Directory src/auth

# Example 2: Fix bug with context
.\smart-code.ps1 -Task "Fix payment bug" -SearchQuery "payment processing" -Files src/payments/processor.py

# Example 3: Refactor code
.\smart-code.ps1 -Task "Refactor duplicate validation logic" -SearchQuery "validate input data" -Directory src
```

## Advanced: Custom Aider Workflow

Create `.aider.conf.yml` in your project:

```yaml
# Auto-generate context before each session
before-commit:
  - python C:/code/aider/code-indexer/src/cli.py map . --output .aider-context.txt

# Always read the context
read:
  - .aider-context.txt

# Ignore patterns match indexer
ignore:
  - node_modules/
  - __pycache__/
  - .venv/
  - dist/
```

Now Aider always has fresh context!

## Best Practices

### 1. Index Regularly

```powershell
# Daily: Quick re-index (only changed files)
python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings

# Weekly: Force re-index everything
python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings --force
```

### 2. Search Before You Code

Always search for similar implementations:
- ✅ Maintains consistency
- ✅ Reuses tested patterns
- ✅ Avoids duplication
- ✅ Faster development

### 3. Use Focused Context

Don't send entire codebase to AI:
- ❌ `--read src/**/*.py` (too much)
- ✅ `--read relevant-map.txt` (just what's needed)

### 4. Combine Multiple Searches

```powershell
# Complex feature? Search multiple aspects
python C:\code\aider\code-indexer\src\cli.py search "database connection" --top-k 3
python C:\code\aider\code-indexer\src\cli.py search "error handling retry" --top-k 3
python C:\code\aider\code-indexer\src\cli.py search "logging configuration" --top-k 3

# Then generate targeted maps
python C:\code\aider\code-indexer\src\cli.py map src/database --output db-context.txt
python C:\code\aider\code-indexer\src\cli.py map src/utils --output utils-context.txt
```

## Measuring Improvement

### Before Code Indexer:
- 🔴 AI generates code not matching your style
- 🔴 Duplicate implementations across codebase
- 🔴 Inconsistent error handling
- 🔴 Wasted tokens sending full files
- 🔴 AI unaware of existing utilities

### After Code Indexer:
- ✅ AI follows your existing patterns
- ✅ Reuses existing utilities
- ✅ Consistent code style
- ✅ 96% token savings with signature-only context
- ✅ AI finds and extends existing code

## Real-World Example

**Scenario**: Add pagination to all API endpoints

**Traditional approach** (30 minutes, inconsistent):
```powershell
wsl aider src/api/*.py --message "Add pagination to all endpoints"
# Result: Each endpoint paginated differently
```

**With Code Indexer** (10 minutes, consistent):
```powershell
# 1. Search for existing pagination
python C:\code\aider\code-indexer\src\cli.py search "pagination page limit offset" --top-k 3

# Found: src/utils/pagination.py with PaginationHelper class!

# 2. Generate API context
python C:\code\aider\code-indexer\src\cli.py map src/api --output api-context.txt

# 3. Generate utility context
python C:\code\aider\code-indexer\src\cli.py map src/utils --output utils-context.txt

# 4. Update all endpoints consistently
wsl aider src/api/*.py `
  --read api-context.txt `
  --read utils-context.txt `
  --message "Add pagination to all endpoints using PaginationHelper from utils"
```

**Result**: Consistent pagination across all endpoints using existing utility.

## Next Steps

1. **Index your project**
   ```powershell
   cd your-project
   python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings
   ```

2. **Create smart-code.ps1** helper script

3. **Start using search before coding**
   - Every new feature: search first
   - Every bug fix: understand context first
   - Every refactor: find duplicates first

4. **Integrate with your workflow**
   - Add to VS Code tasks
   - Create aliases for common commands
   - Set up daily auto-indexing

## Summary

The code indexer makes AI generate better code by:

1. **Understanding your patterns** - AI follows your existing code style
2. **Finding reusable code** - Avoid duplication by finding existing utilities
3. **Providing focused context** - 96% token savings with signature-only maps
4. **Enabling semantic search** - Find relevant code with natural language
5. **Maintaining consistency** - New code matches existing architecture

**Start using it today to 10x your coding productivity!** 🚀
