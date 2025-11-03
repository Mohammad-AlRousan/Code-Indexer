# Enhanced Aider + Code-Indexer Integration Script
# Automatically discovers relevant context before Aider sessions

param(
    [Parameter(Mandatory=$false)]
    [string]$Task = "",
    
    [Parameter(Mandatory=$false)]
    [string]$SearchQuery = "",
    
    [Parameter(Mandatory=$false)]
    [string[]]$Files = @(),
    
    [Parameter(Mandatory=$false)]
    [string]$Directory = ".",
    
    [Parameter(Mandatory=$false)]
    [int]$TopK = 5,
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoAddFiles,
    
    [Parameter(Mandatory=$false)]
    [switch]$GenerateMap,
    
    [Parameter(Mandatory=$false)]
    [switch]$RefreshIndex
)

$ErrorActionPreference = "Stop"
$IndexerPath = "C:\code\Code-Indexer\src\cli.py"

Write-Host "🚀 Smart Aider with Code-Indexer Integration" -ForegroundColor Cyan
Write-Host ""

# Step 1: Refresh index if requested
if ($RefreshIndex) {
    Write-Host "📊 Refreshing code index..." -ForegroundColor Yellow
    python $IndexerPath index $Directory --with-embeddings
    Write-Host ""
}

# Step 2: Search for relevant files if query provided
$discoveredFiles = @()
if ($SearchQuery) {
    Write-Host "🔍 Searching for: $SearchQuery" -ForegroundColor Yellow
    
    $searchResult = python $IndexerPath search $SearchQuery --top-k $TopK 2>&1
    Write-Host $searchResult
    Write-Host ""
    
    # Parse file paths from search results
    $discoveredFiles = $searchResult | Select-String -Pattern "📁\s+(.+)" | ForEach-Object {
        $_.Matches.Groups[1].Value.Trim()
    }
    
    if ($discoveredFiles.Count -gt 0) {
        Write-Host "✅ Found $($discoveredFiles.Count) relevant files" -ForegroundColor Green
        $discoveredFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
        Write-Host ""
    }
}

# Step 3: Generate codebase map if requested
if ($GenerateMap) {
    Write-Host "🗺️  Generating codebase map..." -ForegroundColor Yellow
    python $IndexerPath map $Directory --output ".aider-context.txt"
    Write-Host "✅ Map saved to .aider-context.txt" -ForegroundColor Green
    Write-Host ""
}

# Step 4: Build Aider command
$aiderFiles = @()

# Add explicitly specified files
$aiderFiles += $Files

# Add discovered files (with confirmation or auto)
if ($discoveredFiles.Count -gt 0) {
    if ($AutoAddFiles) {
        $aiderFiles += $discoveredFiles
        Write-Host "✅ Auto-added discovered files" -ForegroundColor Green
    } else {
        Write-Host "Add discovered files to Aider session?" -ForegroundColor Yellow
        foreach ($file in $discoveredFiles) {
            $response = Read-Host "  Add $file? (y/n)"
            if ($response -eq 'y') {
                $aiderFiles += $file
            }
        }
    }
    Write-Host ""
}

# Step 5: Build and run Aider command
$aiderCmd = "wsl aider"

# Add model
$aiderCmd += " --model azure/gpt-4o"

# Add files
if ($aiderFiles.Count -gt 0) {
    $uniqueFiles = $aiderFiles | Select-Object -Unique
    foreach ($file in $uniqueFiles) {
        $aiderCmd += " `"$file`""
    }
}

# Add context map if generated
if ($GenerateMap) {
    $aiderCmd += " --read .aider-context.txt"
}

# Add task message if provided
if ($Task) {
    $aiderCmd += " --message `"$Task`""
}

# Add repo map (Aider's built-in)
$aiderCmd += " --map-tokens 2000"

Write-Host "🤖 Starting Aider with integrated context..." -ForegroundColor Cyan
Write-Host "Command: $aiderCmd" -ForegroundColor Gray
Write-Host ""

# Execute Aider
Invoke-Expression $aiderCmd

Write-Host ""
Write-Host "✅ Session complete!" -ForegroundColor Green
