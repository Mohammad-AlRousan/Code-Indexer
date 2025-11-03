#!/usr/bin/env pwsh
# Smart Code Generation Helper
# Integrates Code Indexer with Aider for context-aware code generation

param(
    [Parameter(Mandatory=$true, HelpMessage="What do you want to build/fix?")]
    [string]$Task,
    
    [Parameter(HelpMessage="Search query to find similar code (optional)")]
    [string]$SearchQuery = "",
    
    [Parameter(HelpMessage="Directory to generate context map from (default: current)")]
    [string]$Directory = ".",
    
    [Parameter(HelpMessage="Specific files to edit")]
    [string[]]$Files = @(),
    
    [Parameter(HelpMessage="Number of similar code results to show")]
    [int]$TopK = 5,
    
    [Parameter(HelpMessage="Skip the search step")]
    [switch]$NoSearch,
    
    [Parameter(HelpMessage="Use cached context (don't regenerate map)")]
    [switch]$UseCache
)

$IndexerPath = "C:\code\aider\code-indexer"
$IndexerExe = "$IndexerPath\.venv\Scripts\python.exe"
$IndexerCli = "$IndexerPath\src\cli.py"
$ContextFile = ".aider-context.txt"

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Smart Code Generation with AI Context   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Task: $Task" -ForegroundColor Green
Write-Host ""

# Step 1: Search for similar code (if query provided)
if ($SearchQuery -and -not $NoSearch) {
    Write-Host "🔍 Searching for similar code..." -ForegroundColor Yellow
    Write-Host "   Query: '$SearchQuery'" -ForegroundColor Gray
    Write-Host ""
    
    & $IndexerExe $IndexerCli search "$SearchQuery" --top-k $TopK
    
    Write-Host ""
    Write-Host "💡 Review the results above to understand existing patterns" -ForegroundColor Cyan
    Write-Host ""
    
    # Ask if user wants to continue
    $continue = Read-Host "Continue with code generation? (Y/n)"
    if ($continue -eq 'n' -or $continue -eq 'N') {
        Write-Host "Aborted by user" -ForegroundColor Yellow
        exit 0
    }
}

# Step 2: Generate context map (unless using cache)
if (-not $UseCache) {
    Write-Host "🗺️  Generating codebase context map..." -ForegroundColor Yellow
    Write-Host "   Directory: $Directory" -ForegroundColor Gray
    Write-Host ""
    
    & $IndexerExe $IndexerCli map $Directory --output $ContextFile
    
    if ($LASTEXITCODE -eq 0) {
        $contextSize = (Get-Item $ContextFile).Length / 1KB
        Write-Host "   ✅ Context map generated ($([math]::Round($contextSize, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to generate context map" -ForegroundColor Red
        exit 1
    }
} else {
    if (Test-Path $ContextFile) {
        Write-Host "📄 Using cached context map" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No cached context found. Run without --UseCache" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🤖 Starting Aider with full context..." -ForegroundColor Green
Write-Host ""

# Step 3: Run Aider with context
$aiderArgs = @(
    "--read", $ContextFile,
    "--message", $Task
)

if ($Files.Count -gt 0) {
    # Add specific files
    $aiderArgs = $Files + $aiderArgs
    $fileList = $Files -join ", "
    Write-Host "   Files: $fileList" -ForegroundColor Gray
}

Write-Host "   Context: $ContextFile" -ForegroundColor Gray
Write-Host "   Task: $Task" -ForegroundColor Gray
Write-Host ""

# Run Aider
wsl aider @aiderArgs

# Step 4: Cleanup (optional - keep context for debugging)
$cleanup = $env:SMART_CODE_CLEANUP
if ($cleanup -eq "true") {
    Remove-Item $ContextFile -ErrorAction SilentlyContinue
    Write-Host "🧹 Cleaned up context file" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green
