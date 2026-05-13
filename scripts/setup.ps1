# Setup script for Windows (PowerShell)
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== into-the-git Setup (Windows) ===" -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python not found. Install Python 3.9+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "[OK] $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Git not found. Install Git from https://git-scm.com" -ForegroundColor Red
    exit 1
}

# Create virtualenv
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[OK] Virtualenv created" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Virtualenv already exists" -ForegroundColor Yellow
}

# Activate and install
Write-Host "Installing dependencies..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\venv\Scripts\python.exe -m pip install -e ".[dev, windows]" --quiet
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Create data directories
New-Item -ItemType Directory -Force -Path "data\repos", "data\reports" | Out-Null

# Verify
Write-Host "Running tests..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m unittest discover tests -v 2>&1 | Select-String -Pattern "^(OK|FAIL|Ran)"

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Activate the virtualenv:  .\venv\Scripts\activate" -ForegroundColor White
Write-Host "Start the app:            python app.py" -ForegroundColor White
Write-Host "Open the dashboard:       http://localhost:5000" -ForegroundColor White
