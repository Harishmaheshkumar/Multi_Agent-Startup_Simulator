# Setup script for Multi-Agent Startup Simulator
# This script sets up the development environment on Windows

Write-Host "Setting up Multi-Agent Startup Simulator..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
} catch {
    Write-Host "Python is not installed. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

Write-Host "Python found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data/conversations", "data/embeddings", "data/logs", "data/startups" | Out-Null

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Environment Configuration
OLLAMA_BASE_URL=http://localhost:11434
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
MAX_TOKENS=4096
TEMPERATURE=0.7

# Vector Store Settings
VECTOR_DIMENSION=384
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# CrewAI Settings
MAX_ITERATIONS=10
VERBOSE=True
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "Created .env file. Please edit it with your API keys." -ForegroundColor Cyan
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run 'python run.py' to start the application." -ForegroundColor Green