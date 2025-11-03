#!/usr/bin/env pwsh
# Setup script for Code Indexer

Write-Host "🚀 Setting up Code Indexer..." -ForegroundColor Cyan

# Check Python version
Write-Host "`n📌 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found $pythonVersion" -ForegroundColor Green

# Create virtual environment
Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "⚠️  .venv already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`n📥 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create .env if it doesn't exist
Write-Host "`n⚙️  Configuring environment..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "⚠️  .env already exists, skipping..." -ForegroundColor Yellow
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env with your Azure OpenAI credentials" -ForegroundColor Yellow
}

# Success message
Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env with your Azure OpenAI credentials" -ForegroundColor White
Write-Host "2. Activate the virtual environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "3. Index your code: python src\cli.py index ." -ForegroundColor White
Write-Host "4. Search: python src\cli.py search ""your query""" -ForegroundColor White
Write-Host "`nFor more info: cat README.md" -ForegroundColor White
