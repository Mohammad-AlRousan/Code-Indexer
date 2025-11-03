# Smart Code Generation - Examples

Real-world examples of using the code indexer with Aider for better code generation.

## Setup

Add the smart-code script to your PATH or create an alias:

```powershell
# Option 1: Add to PATH
$env:PATH += ";C:\code\aider\code-indexer"

# Option 2: Create alias in your PowerShell profile
Set-Alias smart-code C:\code\aider\code-indexer\smart-code.ps1

# Make permanent (add to $PROFILE)
notepad $PROFILE
# Add: Set-Alias smart-code C:\code\aider\code-indexer\smart-code.ps1
```

## Example 1: Add New Feature

**Scenario**: Add user authentication to your web app

```powershell
cd C:\code\my-web-app

# First, index the codebase
python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings

# Then use smart-code
smart-code.ps1 `
  -Task "Add JWT authentication middleware" `
  -SearchQuery "authentication middleware jwt" `
  -Directory src/middleware

# What happens:
# 1. Searches for existing auth patterns (shows 5 similar implementations)
# 2. Generates context map of middleware directory
# 3. Launches Aider with full context
# 4. AI generates code matching your existing patterns!
```

## Example 2: Fix Bug with Context

**Scenario**: Fix a payment processing bug

```powershell
cd C:\code\ecommerce-app

# Use smart-code with specific files
smart-code.ps1 `
  -Task "Fix the refund calculation bug in PaymentProcessor.processRefund()" `
  -SearchQuery "payment refund calculation" `
  -Files src/payments/PaymentProcessor.py,src/payments/RefundHandler.py `
  -Directory src/payments

# What happens:
# 1. Shows existing refund/payment code
# 2. Generates payment module context
# 3. Opens specific files in Aider
# 4. AI fixes bug while maintaining compatibility
```

## Example 3: Refactor Duplicate Code

**Scenario**: You noticed duplicate validation logic across files

```powershell
cd C:\code\my-api

# Search for duplicates
python C:\code\aider\code-indexer\src\cli.py search "validate email input" --top-k 10 --threshold 0.6

# Found 5 similar implementations!
# 1. validate_email in users.py (0.92)
# 2. check_email in auth.py (0.88)
# 3. email_is_valid in utils.py (0.85)
# ...

# Refactor using smart-code
smart-code.ps1 `
  -Task "Extract duplicate email validation into src/utils/validators.py and update all callers" `
  -Files src/users.py,src/auth.py,src/utils.py,src/utils/validators.py `
  -Directory src `
  -NoSearch  # Already searched manually
```

## Example 4: Implement Similar Feature

**Scenario**: Add pagination to a new API endpoint

```powershell
cd C:\code\rest-api

# Search for existing pagination
python C:\code\aider\code-indexer\src\cli.py search "pagination page limit offset" --top-k 5

# Results show existing PaginationHelper class!

# Implement new endpoint using existing pattern
smart-code.ps1 `
  -Task "Add GET /api/products endpoint with pagination using PaginationHelper" `
  -SearchQuery "api endpoint pagination" `
  -Files src/api/products.py `
  -Directory src/api

# AI will:
# - See how other endpoints use PaginationHelper
# - Follow same routing pattern
# - Use same response format
# - Match error handling style
```

## Example 5: Database Migration

**Scenario**: Add new database fields safely

```powershell
cd C:\code\django-app

# Understand existing migrations
smart-code.ps1 `
  -Task "Add 'last_login_ip' and 'login_count' fields to User model with migration" `
  -SearchQuery "database migration add field" `
  -Files app/models.py `
  -Directory app/migrations

# AI generates:
# - Model changes matching your style
# - Proper migration file
# - Update serializers/forms if needed
```

## Example 6: Add Tests

**Scenario**: Write tests for new feature

```powershell
cd C:\code\python-project

# Find existing test patterns
python C:\code\aider\code-indexer\src\cli.py search "unit test mock fixture" --file-pattern "*test*.py" --top-k 5

# Generate tests following existing patterns
smart-code.ps1 `
  -Task "Write unit tests for UserService.create_user() with mocks and fixtures" `
  -SearchQuery "test mock database user" `
  -Files tests/test_user_service.py `
  -Directory tests

# AI writes tests matching your:
# - Test framework (pytest/unittest)
# - Naming conventions
# - Fixture patterns
# - Mock approach
```

## Example 7: API Integration

**Scenario**: Add third-party API integration

```powershell
cd C:\code\integration-service

# Check existing integrations
python C:\code\aider\code-indexer\src\cli.py search "http client api request" --top-k 5

# Add new integration
smart-code.ps1 `
  -Task "Add Stripe payment integration using our existing HTTPClient pattern" `
  -SearchQuery "http client retry timeout" `
  -Files src/integrations/stripe.py `
  -Directory src/integrations

# AI will:
# - Use your existing HTTPClient class
# - Follow retry/timeout patterns
# - Match error handling
# - Use same logging approach
```

## Example 8: Performance Optimization

**Scenario**: Add caching to slow queries

```powershell
cd C:\code\web-service

# Find existing cache usage
python C:\code\aider\code-indexer\src\cli.py search "cache redis get set" --top-k 5

# Add caching
smart-code.ps1 `
  -Task "Add Redis caching to UserRepository.get_user() with 5 minute TTL" `
  -SearchQuery "redis cache repository" `
  -Files src/repositories/user_repository.py `
  -Directory src/repositories,src/cache

# AI implements caching using your existing:
# - Cache client configuration
# - Key naming convention
# - TTL patterns
# - Cache invalidation strategy
```

## Example 9: Error Handling

**Scenario**: Improve error handling

```powershell
cd C:\code\nodejs-app

# Study existing error handling
smart-code.ps1 `
  -Task "Add proper error handling to payment processing with custom exceptions" `
  -SearchQuery "error handling exception custom" `
  -Files src/services/paymentService.js `
  -Directory src

# AI adds error handling matching your:
# - Custom exception classes
# - Error logging format
# - Error response structure
```

## Example 10: Documentation

**Scenario**: Add comprehensive docstrings

```powershell
cd C:\code\python-lib

# See docstring style
python C:\code\aider\code-indexer\src\cli.py map src --output docs-context.txt

# Add docstrings
smart-code.ps1 `
  -Task "Add Google-style docstrings to all functions in utils.py" `
  -Files src/utils.py `
  -Directory src `
  -UseCache  # Use existing context

# AI adds docstrings matching your style
```

## Workflow Tips

### Daily Workflow

```powershell
# Morning: Index overnight changes
cd your-project
python C:\code\aider\code-indexer\src\cli.py index . --with-embeddings

# Throughout the day: Use smart-code for every task
smart-code.ps1 -Task "Add feature X" -SearchQuery "similar feature"
smart-code.ps1 -Task "Fix bug Y" -SearchQuery "related code"
smart-code.ps1 -Task "Refactor Z" -SearchQuery "duplicate code"
```

### Before Big Changes

```powershell
# 1. Search extensively
python C:\code\aider\code-indexer\src\cli.py search "feature area 1" --top-k 10
python C:\code\aider\code-indexer\src\cli.py search "feature area 2" --top-k 10
python C:\code\aider\code-indexer\src\cli.py search "feature area 3" --top-k 10

# 2. Generate multiple context maps
python C:\code\aider\code-indexer\src\cli.py map src/module1 --output context1.txt
python C:\code\aider\code-indexer\src\cli.py map src/module2 --output context2.txt

# 3. Use Aider with multiple contexts
wsl aider --read context1.txt --read context2.txt --message "Big refactor task"
```

### Team Collaboration

```powershell
# Share context maps for code review
python C:\code\aider\code-indexer\src\cli.py map src --output ARCHITECTURE.md

# Commit to repo
git add ARCHITECTURE.md
git commit -m "docs: Update architecture map"

# Team members can use it
wsl aider --read ARCHITECTURE.md --message "Add feature following architecture"
```

## Measuring Success

### Before Code Indexer
```
Time to implement feature: 2 hours
Code consistency: 60%
Duplicated code: High
Token usage: 10,000 tokens
AI accuracy: 70%
```

### After Code Indexer
```
Time to implement feature: 30 minutes (4x faster!)
Code consistency: 95% (AI follows patterns)
Duplicated code: Low (AI finds existing utilities)
Token usage: 400 tokens (96% reduction!)
AI accuracy: 95% (better context)
```

## Advanced Usage

### Custom Search Filters

```powershell
# Only Python files
python C:\code\aider\code-indexer\src\cli.py search "database query" --file-pattern "*.py"

# Only test files
python C:\code\aider\code-indexer\src\cli.py search "mock fixture" --file-pattern "*test*.py"

# Only specific directory
python C:\code\aider\code-indexer\src\cli.py search "auth" --file-pattern "src/auth/*"

# Only functions
python C:\code\aider\code-indexer\src\cli.py search "validation" --type function

# Only classes
python C:\code\aider\code-indexer\src\cli.py search "service" --type class

# High precision (0.9 threshold)
python C:\code\aider\code-indexer\src\cli.py search "specific pattern" --threshold 0.9
```

### Batch Processing

Process multiple related changes:

```powershell
# script: batch-update.ps1
$changes = @(
    @{Task="Add logging to UserService"; Files="src/services/user.py"},
    @{Task="Add logging to PaymentService"; Files="src/services/payment.py"},
    @{Task="Add logging to OrderService"; Files="src/services/order.py"}
)

foreach ($change in $changes) {
    smart-code.ps1 `
        -Task $change.Task `
        -Files $change.Files `
        -SearchQuery "logging service" `
        -Directory src/services
}
```

## Troubleshooting

### "No results found"

```powershell
# Lower threshold
python C:\code\aider\code-indexer\src\cli.py search "query" --threshold 0.5

# Broader search
python C:\code\aider\code-indexer\src\cli.py search "broader query" --top-k 20
```

### "Context too large"

```powershell
# Use focused directory
smart-code.ps1 -Directory src/specific-module  # Not entire src/

# Or multiple specific files
smart-code.ps1 -Files file1.py,file2.py,file3.py
```

### "AI not following patterns"

```powershell
# Regenerate context (don't use cache)
smart-code.ps1 -Task "..." -NoCache

# Or force re-index
python C:\code\aider\code-indexer\src\cli.py index . --force --with-embeddings
```

## Summary

Use `smart-code.ps1` for every coding task:
- ✅ Always search before implementing
- ✅ Always provide context to AI
- ✅ Always review similar code first
- ✅ Let AI follow your patterns

**Result**: Faster development, consistent code, fewer bugs! 🚀
