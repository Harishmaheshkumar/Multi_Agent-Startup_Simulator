#!/usr/bin/env pwsh
<#
.SYNOPSIS
Start the Multi-Agent Startup Simulator application

.DESCRIPTION
Activates the Python virtual environment and runs the application with Groq LLM support.

.EXAMPLE
.\START.ps1
#>

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Multi-Agent Startup Simulator" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if .venv exists
if (-not (Test-Path ".\.venv")) {
    Write-Host "❌ Virtual environment not found. Please run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating Python virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Check if GROQ_API_KEY is set
if (-not $env:GROQ_API_KEY) {
    Write-Host "⚠️  GROQ_API_KEY environment variable not set." -ForegroundColor Yellow
    Write-Host "   The app will use Ollama if available, or fall back to in-memory mode." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "✓ Environment ready" -ForegroundColor Green
Write-Host ""
Write-Host "📍 API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 UI Server: http://localhost:8501 (if enabled)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Run the application
python run.py
