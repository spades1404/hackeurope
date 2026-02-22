<#
.SYNOPSIS
    Starts the TunaTax end-to-end demo.
.DESCRIPTION
    This script tries to use Docker Compose for the backend. If Docker is not available,
    it falls back to running the Python backend locally in a new window.
    It then installs frontend dependencies (if necessary) and starts the Vite frontend.
#>

$ErrorActionPreference = "Stop"

Write-Host "-> Starting TunaTax Demo Setup..." -ForegroundColor Cyan

$UseDocker = $false

# Check for Docker
try {
    docker --version | Out-Null
    Write-Host "[OK] Docker is installed." -ForegroundColor Green
    $UseDocker = $true
} catch {
    Write-Host "[Info] Docker is not installed or not running. Falling back to local Python backend." -ForegroundColor Yellow
}

# 1. Start Backend
if ($UseDocker) {
    Write-Host "`n-> Starting Backend via Docker Compose..." -ForegroundColor Cyan
    if (Test-Path "docker-compose.yml") {
        # Build and start in detached mode
        docker-compose up -d --build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[Error] Failed to start docker container." -ForegroundColor Red
            exit 1
        }
        Write-Host "[OK] Backend is running in Docker (Port 8000)." -ForegroundColor Green
    } else {
        Write-Host "[Error] docker-compose.yml not found." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n-> Starting Backend via Local Python..." -ForegroundColor Cyan
    
    # Check Python
    try {
        python --version | Out-Null
    } catch {
        Write-Host "[Error] Python is not installed. Please install Python or Docker." -ForegroundColor Red
        exit 1
    }

    # Setup venv
    if (-not (Test-Path ".venv")) {
        Write-Host "-> Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
    }

    # Determine activation script path
    $VenvActivate = ".\.venv\Scripts\Activate.ps1"
    
    # Run pip install and start server in a new window
    Write-Host "-> Starting Python backend server in a new window..." -ForegroundColor Yellow
    
    # Create a temporary script for the backend window
    $BackendScript = @"
`$ErrorActionPreference = 'Stop'
`$env:PYTHONPATH = '.'
& '$VenvActivate'
Write-Host "-> Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "-> Starting FastAPI server..." -ForegroundColor Green
python -m backend.main
"@
    $TmpScript = Join-Path $env:TEMP "tunatax_backend.ps1"
    Set-Content -Path $TmpScript -Value $BackendScript
    
    Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$TmpScript`""
    
    Write-Host "[OK] Backend started. (Check the new PowerShell window for logs)" -ForegroundColor Green
}

# 2. Setup Frontend
Write-Host "`n-> Setting up Frontend..." -ForegroundColor Cyan
$FrontendDir = "frontend_figma"

if (-not (Test-Path $FrontendDir)) {
    Write-Host "[Error] Frontend directory '$FrontendDir' not found." -ForegroundColor Red
    exit 1
}

Push-Location $FrontendDir

# Check if npm is installed
try {
    npm --version | Out-Null
} catch {
    Write-Host "[Error] Node.js (npm) is not installed. Please install Node.js." -ForegroundColor Red
    Pop-Location
    exit 1
}

# Install dependencies if node_modules doesn't exist
if (-not (Test-Path "node_modules")) {
    Write-Host "-> Installing frontend dependencies (this might take a minute)..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Error] Failed to install frontend dependencies." -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "[OK] Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "[OK] Frontend dependencies already installed." -ForegroundColor Green
}

# 3. Start Frontend
Write-Host "`n-> Starting Vite Development Server..." -ForegroundColor Cyan
Write-Host "The application will be available at http://localhost:5173" -ForegroundColor Yellow
Write-Host "The admin demo page will be available at http://localhost:5173/admin" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the frontend server.`n" -ForegroundColor DarkGray

# Run vite dev server (this blocks the terminal)
npm run dev

Pop-Location
