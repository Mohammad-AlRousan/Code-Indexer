# Using Code Indexer for Security & Architecture Compliance

## Overview

Instead of building a full RAG (Retrieval Augmented Generation) system, you can use Code Indexer to ensure your codebase and PRs comply with security design and architecture guidelines.

## How It Works

### Traditional RAG Approach (Complex)
```
Guidelines → Chunking → Embeddings → Vector DB → Query → Context → LLM → Response
```

### Code Indexer Approach (Simple)
```
1. Index your codebase + guidelines
2. Search for similar patterns
3. Generate context map with relevant code
4. Use with AI to verify compliance
```

## Setup Guide

### Step 1: Organize Your Guidelines

Create a `guidelines/` directory with your standards:

```
project/
├── guidelines/
│   ├── security/
│   │   ├── authentication.md
│   │   ├── data_validation.md
│   │   ├── encryption.md
│   │   └── api_security.md
│   ├── architecture/
│   │   ├── database_patterns.md
│   │   ├── error_handling.md
│   │   ├── logging_standards.md
│   │   └── service_design.md
│   └── code_standards/
│       ├── naming_conventions.md
│       └── code_review_checklist.md
├── src/
└── ...
```

**Example**: `guidelines/security/authentication.md`
```markdown
# Authentication Security Guidelines

## ✅ Required Patterns

### Always use centralized auth service
```python
# ✅ CORRECT
from auth.service import AuthService

def protected_endpoint(request):
    user = AuthService.verify_token(request.headers['Authorization'])
    if not user:
        raise Unauthorized()
```

### Never implement custom auth
```python
# ❌ WRONG - Custom auth implementation
def my_custom_auth(username, password):
    if password == "admin123":  # Security violation!
        return True
```

## Required Checks
- All endpoints must validate JWT tokens
- Passwords must be hashed with bcrypt (min 12 rounds)
- Session tokens must expire within 1 hour
- Multi-factor auth required for admin actions
```

### Step 2: Convert Guidelines to Code Examples

Create reference implementations in `guidelines/examples/`:

```python
# guidelines/examples/secure_api_endpoint.py
"""
Reference: Secure API Endpoint Pattern
Complies with: security/authentication.md, architecture/error_handling.md
"""

from auth.service import AuthService
from decorators import require_auth, validate_input
from exceptions import Unauthorized, ValidationError
from logging import get_logger

logger = get_logger(__name__)

@require_auth
@validate_input(UserSchema)
def create_user(request):
    """
    ✅ COMPLIANT: Shows proper auth, validation, error handling, logging
    """
    try:
        # Validate authentication
        user = AuthService.verify_token(request.headers['Authorization'])
        
        # Validate input
        data = UserSchema.validate(request.json)
        
        # Business logic
        new_user = UserService.create(data)
        
        # Audit logging
        logger.info(f"User created: {new_user.id} by {user.id}")
        
        return {"id": new_user.id}, 201
        
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return {"error": str(e)}, 400
    except Unauthorized as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {"error": "Unauthorized"}, 401
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500
```

### Step 3: Index Everything Together

```bash
# Index both codebase AND guidelines
python code-indexer/src/cli.py index . --with-embeddings

# This indexes:
# - Your source code (src/)
# - Your guidelines (guidelines/)
# - Reference examples (guidelines/examples/)
```

## Usage Workflows

### Workflow 1: Pre-PR Compliance Check

**Check a new feature branch before creating PR:**

```powershell
# 1. Search for similar patterns in your code
python code-indexer/src/cli.py search "authentication endpoint with JWT validation" --top-k 5

# Returns:
# 1. AuthService.verify_token (0.89) - guidelines/examples/secure_api_endpoint.py
# 2. protected_route decorator (0.85) - src/auth/decorators.py
# 3. authenticate_user (0.81) - src/api/auth.py
```

```powershell
# 2. Generate context map for your new code
python code-indexer/src/cli.py map src/api/new_feature.py --output context.txt
```

```powershell
# 3. Use AI to verify compliance
wsl aider src/api/new_feature.py `
  --read context.txt `
  --read guidelines/security/authentication.md `
  --message "Review this code against our authentication security guidelines. List any violations."
```

**AI Response:**
```
Reviewing src/api/new_feature.py against authentication guidelines...

❌ VIOLATIONS FOUND:

1. Line 45: Custom password validation
   - Guideline: Always use AuthService.verify_token()
   - Current: if user.password == hash(password)
   - Fix: Use AuthService.verify_token(request.headers['Authorization'])

2. Line 67: Missing session expiration
   - Guideline: Session tokens must expire within 1 hour
   - Current: session = create_session(user, expires=None)
   - Fix: session = create_session(user, expires=timedelta(hours=1))

3. Line 89: No audit logging
   - Guideline: All auth actions must be logged
   - Fix: Add logger.info(f"User authenticated: {user.id}")

✅ COMPLIANT:
- JWT token validation present
- bcrypt password hashing (12 rounds)
- Proper error handling
```

### Workflow 2: PR Review Automation

**Automated PR compliance check script:**

```powershell
# check-pr-compliance.ps1

param(
    [string]$PrBranch,
    [string]$BaseBranch = "main"
)

# Get changed files
$changedFiles = git diff --name-only $BaseBranch...$PrBranch | Where-Object { $_ -match '\.(py|js|ts)$' }

Write-Host "🔍 Checking $($changedFiles.Count) changed files for compliance..." -ForegroundColor Cyan

foreach ($file in $changedFiles) {
    Write-Host "`n📄 Analyzing: $file" -ForegroundColor Yellow
    
    # Determine what guidelines apply
    $guidelines = @()
    
    if ($file -match "api/|endpoint/|routes/") {
        $guidelines += "guidelines/security/api_security.md"
        $guidelines += "guidelines/architecture/error_handling.md"
    }
    
    if ($file -match "auth/|login/|session/") {
        $guidelines += "guidelines/security/authentication.md"
    }
    
    if ($file -match "database/|models/|dao/") {
        $guidelines += "guidelines/security/data_validation.md"
        $guidelines += "guidelines/architecture/database_patterns.md"
    }
    
    # Search for similar compliant examples
    Write-Host "  Finding reference implementations..." -ForegroundColor Gray
    $similar = python code-indexer/src/cli.py search "$(Split-Path -Leaf $file)" --top-k 3 --file-pattern "guidelines/examples/*"
    
    # Generate context map
    python code-indexer/src/cli.py map $file --output "temp-pr-context.txt"
    
    # AI compliance check
    $guidelineArgs = $guidelines | ForEach-Object { "--read $_" }
    
    Write-Host "  🤖 Running AI compliance check..." -ForegroundColor Gray
    wsl aider $file --read temp-pr-context.txt $guidelineArgs `
        --message "Review this file against our security and architecture guidelines. Output ONLY violations in this format: [VIOLATION] Line X: Description. If compliant, output: [COMPLIANT]" `
        --yes > "pr-check-$($file.Replace('/','-')).txt"
    
    # Parse results
    $violations = Get-Content "pr-check-$($file.Replace('/','-')).txt" | Select-String "\[VIOLATION\]"
    
    if ($violations) {
        Write-Host "  ❌ $($violations.Count) violation(s) found" -ForegroundColor Red
        $violations | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
    } else {
        Write-Host "  ✅ Compliant" -ForegroundColor Green
    }
}

# Cleanup
Remove-Item temp-pr-context.txt -ErrorAction SilentlyContinue
```

**Usage:**
```powershell
# Check current PR
.\check-pr-compliance.ps1 -PrBranch "feature/new-api-endpoint"

# Output:
# 🔍 Checking 3 changed files for compliance...
# 
# 📄 Analyzing: src/api/users.py
#   Finding reference implementations...
#   🤖 Running AI compliance check...
#   ❌ 2 violation(s) found
#      [VIOLATION] Line 45: Missing input validation
#      [VIOLATION] Line 67: Logging PII data
#
# 📄 Analyzing: src/auth/middleware.py
#   ✅ Compliant
```

### Workflow 3: Real-time Compliance Checking (VS Code)

**Create a VS Code task** (`.vscode/tasks.json`):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Check Compliance",
      "type": "shell",
      "command": "python",
      "args": [
        "${workspaceFolder}/scripts/compliance-check.py",
        "${file}"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

**Script** (`scripts/compliance-check.py`):

```python
#!/usr/bin/env python3
import sys
import subprocess
import json
from pathlib import Path

def check_compliance(file_path):
    """Check single file compliance using Code Indexer"""
    
    # Search for similar compliant patterns
    result = subprocess.run([
        'python', 'code-indexer/src/cli.py', 
        'search', f'compliant example similar to {Path(file_path).name}',
        '--file-pattern', 'guidelines/examples/*',
        '--top-k', '3'
    ], capture_output=True, text=True)
    
    print("🔍 Similar compliant examples:")
    print(result.stdout)
    
    # Determine applicable guidelines
    guidelines = []
    file_lower = file_path.lower()
    
    if 'api' in file_lower or 'endpoint' in file_lower:
        guidelines.extend([
            'guidelines/security/api_security.md',
            'guidelines/architecture/error_handling.md'
        ])
    
    if 'auth' in file_lower:
        guidelines.append('guidelines/security/authentication.md')
    
    if 'database' in file_lower or 'model' in file_lower:
        guidelines.extend([
            'guidelines/security/data_validation.md',
            'guidelines/architecture/database_patterns.md'
        ])
    
    if not guidelines:
        print("ℹ️  No specific guidelines apply to this file")
        return
    
    print(f"\n📋 Applicable guidelines: {', '.join(guidelines)}")
    
    # Generate context
    subprocess.run([
        'python', 'code-indexer/src/cli.py',
        'map', file_path,
        '--output', 'temp-compliance-context.txt'
    ])
    
    # AI check
    guideline_args = []
    for g in guidelines:
        guideline_args.extend(['--read', g])
    
    print("\n🤖 Running compliance check...\n")
    
    subprocess.run([
        'wsl', 'aider', file_path,
        '--read', 'temp-compliance-context.txt',
        *guideline_args,
        '--message', 'Check compliance with guidelines. List violations or confirm compliance.'
    ])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: compliance-check.py <file>")
        sys.exit(1)
    
    check_compliance(sys.argv[1])
```

### Workflow 4: Find Non-Compliant Code in Existing Codebase

**Search for anti-patterns:**

```powershell
# Find custom authentication implementations (violates guidelines)
python code-indexer/src/cli.py search "custom password validation login authentication" `
  --file-pattern "src/**" `
  --top-k 10

# Find missing error handling
python code-indexer/src/cli.py search "function without try catch exception handling" `
  --file-pattern "src/api/**" `
  --top-k 10

# Find potential SQL injection vulnerabilities
python code-indexer/src/cli.py search "SQL query string concatenation" `
  --file-pattern "src/**" `
  --top-k 10
```

**Then fix them:**

```powershell
# For each violation found
$violations = @("src/api/legacy_auth.py", "src/db/queries.py")

foreach ($file in $violations) {
    # Generate context with compliant examples
    python code-indexer/src/cli.py map $file --output context.txt
    
    # Search for compliant pattern
    python code-indexer/src/cli.py search "secure $(Split-Path -Leaf $file)" `
      --file-pattern "guidelines/examples/*" `
      --top-k 1 `
      > reference.txt
    
    # Use AI to refactor
    wsl aider $file `
      --read context.txt `
      --read reference.txt `
      --read guidelines/security/authentication.md `
      --message "Refactor this code to comply with our security guidelines. Use the reference implementation as a guide."
}
```

## Advanced: Compliance Dashboard

**Create a compliance report:**

```python
# compliance-report.py

import subprocess
import json
from pathlib import Path
from collections import defaultdict

def generate_compliance_report():
    """Generate compliance report for entire codebase"""
    
    # Get all source files
    src_files = list(Path('src').rglob('*.py'))
    
    report = {
        'total_files': len(src_files),
        'violations': defaultdict(list),
        'compliant': [],
        'by_category': defaultdict(int)
    }
    
    for file in src_files:
        print(f"Checking {file}...")
        
        # Search for anti-patterns
        checks = {
            'auth': "custom authentication password hardcoded",
            'sql': "SQL injection string concatenation",
            'logging': "logging sensitive data PII",
            'error': "bare except clause missing error handling"
        }
        
        file_violations = []
        
        for category, query in checks.items():
            result = subprocess.run([
                'python', 'code-indexer/src/cli.py',
                'search', query,
                '--file-pattern', str(file),
                '--threshold', '0.7'
            ], capture_output=True, text=True)
            
            if 'Found' in result.stdout and '0 results' not in result.stdout:
                file_violations.append(category)
                report['by_category'][category] += 1
        
        if file_violations:
            report['violations'][str(file)] = file_violations
        else:
            report['compliant'].append(str(file))
    
    # Generate report
    print("\n" + "="*60)
    print("COMPLIANCE REPORT")
    print("="*60)
    print(f"\nTotal Files: {report['total_files']}")
    print(f"Compliant: {len(report['compliant'])} ({len(report['compliant'])/report['total_files']*100:.1f}%)")
    print(f"Violations: {len(report['violations'])} ({len(report['violations'])/report['total_files']*100:.1f}%)")
    
    print("\n📊 Violations by Category:")
    for category, count in sorted(report['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    print("\n❌ Files with Violations:")
    for file, categories in sorted(report['violations'].items()):
        print(f"  {file}: {', '.join(categories)}")
    
    # Save detailed report
    with open('compliance-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n💾 Detailed report saved to compliance-report.json")

if __name__ == '__main__':
    generate_compliance_report()
```

## Key Advantages Over RAG

| Aspect | RAG System | Code Indexer |
|--------|-----------|--------------|
| **Setup Time** | Days/weeks (vector DB, chunking, embeddings) | Minutes (just index) |
| **Maintenance** | Complex (vector DB management) | Simple (SQLite cache) |
| **Query Speed** | Depends on vector DB | < 2 seconds |
| **Context Quality** | Generic chunks | Exact code signatures |
| **Code Understanding** | Limited | Full AST parsing |
| **Integration** | Custom API needed | Works with Aider directly |
| **Cost** | Vector DB hosting | Local SQLite only |
| **Token Efficiency** | 100% of chunks | 4% (96% reduction) |

## Best Practices

### 1. Keep Guidelines as Code Examples

Instead of prose, write executable examples:

❌ **Bad** (prose guidelines):
```markdown
Endpoints should validate authentication using JWT tokens
```

✅ **Good** (code examples):
```python
# guidelines/examples/secure_endpoint.py
@require_auth  # ✅ Shows exact pattern
def endpoint(request):
    user = AuthService.verify_token(request.headers['Authorization'])
```

### 2. Index Regularly

```bash
# Daily cron job
0 2 * * * cd /project && python code-indexer/src/cli.py index . --with-embeddings
```

### 3. Use with Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts)$')

if [ -n "$STAGED_FILES" ]; then
    echo "🔍 Checking compliance..."
    python scripts/compliance-check.py $STAGED_FILES
    
    if [ $? -ne 0 ]; then
        echo "❌ Compliance check failed. Commit aborted."
        exit 1
    fi
fi
```

### 4. Track Compliance Metrics

```python
# Track compliance over time
{
  "2025-11-01": {"compliant": 85, "violations": 15, "compliance_rate": 85.0},
  "2025-11-02": {"compliant": 87, "violations": 13, "compliance_rate": 87.0},
  "2025-11-03": {"compliant": 90, "violations": 10, "compliance_rate": 90.0}
}
```

## Summary

**Code Indexer replaces RAG for compliance checking by:**

1. ✅ **Indexing guidelines alongside code** - Guidelines become searchable reference implementations
2. ✅ **Semantic search** - Find similar compliant/non-compliant patterns
3. ✅ **Context generation** - AI gets relevant code + guidelines together
4. ✅ **Automated checks** - PR reviews, pre-commit hooks, CI/CD integration
5. ✅ **Simple setup** - No vector database, no chunking, no complex RAG pipeline

**Result**: Faster, simpler, and more accurate compliance verification without building a full RAG system! 🚀
