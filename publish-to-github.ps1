# GitHub Publishing Helper Script
# Quick commands to commit and push to GitHub

Write-Host "=== Code-Indexer GitHub Publishing ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Show status
Write-Host "Step 1: Current Git Status" -ForegroundColor Yellow
git status --short
Write-Host ""

# Step 2: Stage all files
Write-Host "Step 2: Staging all files..." -ForegroundColor Yellow
git add .
Write-Host "✅ Files staged" -ForegroundColor Green
Write-Host ""

# Step 3: Commit
Write-Host "Step 3: Committing changes..." -ForegroundColor Yellow
$commitMessage = @"
feat: add comprehensive Aider integration and GitHub-ready files

Core Integration Features:
- Add Aider plugin with /index-search, /index-map, /index-refresh commands
- Add smart wrapper PowerShell script for automated context discovery
- Add REST API server (Flask) for multi-tool integration
- Add VS Code extension scaffold (package.json + extension.ts)
- Add git pre-commit hook for auto-indexing

Documentation:
- Add docs/AIDER-INTEGRATION.md (complete 300+ line guide)
- Add INTEGRATION-SUMMARY.md (quick reference)
- Add aider_plugin/README.md (plugin setup guide)
- Update README.md with GitHub badges and integration info

GitHub Configuration:
- Add .github/workflows/test.yml (CI/CD for Python 3.8-3.12)
- Add .github/workflows/security.yml (Snyk security scanning)
- Add .github/PULL_REQUEST_TEMPLATE.md
- Add .github/ISSUE_TEMPLATE/ (bug, feature, aider integration)
- Add .github/repository-metadata.yml (topics and metadata)

Project Files:
- Update .gitignore (Aider files, VS Code extension build)
- Update requirements.txt (add flask, flask-cors)
- Keep SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE

Integration Benefits:
- Semantic search complements Aider's dependency-based repo map
- 5 different integration methods for various workflows
- Full codebase indexing with persistent cache
- Natural language code discovery

Tested:
- CLI commands (index, map, stats) ✓
- Python syntax validation ✓
- All integration files created ✓
- Ready for GitHub publication ✓
"@

git commit -m $commitMessage
Write-Host "✅ Changes committed" -ForegroundColor Green
Write-Host ""

# Step 4: Show next steps
Write-Host "Step 4: Next Steps" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option A: Push to existing remote" -ForegroundColor Cyan
Write-Host "  git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "Option B: Add remote and push (if new repo)" -ForegroundColor Cyan
Write-Host "  git remote add origin https://github.com/Mohammad-AlRousan/Code-Indexer.git" -ForegroundColor White
Write-Host "  git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "Option C: Create tag and push" -ForegroundColor Cyan
Write-Host "  git tag -a v0.1.0 -m 'Initial release with Aider integration'" -ForegroundColor White
Write-Host "  git push origin v0.1.0" -ForegroundColor White
Write-Host ""

# Ask user
$response = Read-Host "Push to origin/main now? (y/n)"
if ($response -eq 'y') {
    Write-Host "`nPushing to origin/main..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host ""
        Write-Host "View your repository at:" -ForegroundColor Cyan
        Write-Host "https://github.com/Mohammad-AlRousan/Code-Indexer" -ForegroundColor White
        Write-Host ""
        Write-Host "Next: Create a release at:" -ForegroundColor Cyan
        Write-Host "https://github.com/Mohammad-AlRousan/Code-Indexer/releases/new" -ForegroundColor White
    } else {
        Write-Host "❌ Push failed. Check the error above." -ForegroundColor Red
        Write-Host ""
        Write-Host "If remote doesn't exist, run:" -ForegroundColor Yellow
        Write-Host "  git remote add origin https://github.com/Mohammad-AlRousan/Code-Indexer.git" -ForegroundColor White
        Write-Host "  git push -u origin main" -ForegroundColor White
    }
} else {
    Write-Host "`n✅ Commit ready. Push when you're ready:" -ForegroundColor Green
    Write-Host "  git push origin main" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 See PUBLISHING.md for full publishing guide" -ForegroundColor Cyan
