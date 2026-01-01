# PowerShell script to run integration tests in Docker Compose environment

$ErrorActionPreference = "Stop"

Write-Host "Starting services with Docker Compose..." -ForegroundColor Green
docker-compose up -d

Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Wait for backend to be ready
Write-Host "Waiting for backend to be ready..." -ForegroundColor Yellow
$timeout = 60
$elapsed = 0
$backendReady = $false

while ($elapsed -lt $timeout) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "Backend is ready!" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {
        # Service not ready yet
    }
    Write-Host "Waiting for backend..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if (-not $backendReady) {
    Write-Host "ERROR: Backend did not become ready in time" -ForegroundColor Red
    docker-compose logs backend
    docker-compose down
    exit 1
}

# Wait for frontend to be ready
Write-Host "Waiting for frontend to be ready..." -ForegroundColor Yellow
$elapsed = 0
$frontendReady = $false

while ($elapsed -lt $timeout) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "Frontend is ready!" -ForegroundColor Green
            $frontendReady = $true
            break
        }
    } catch {
        # Service not ready yet
    }
    Write-Host "Waiting for frontend..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if (-not $frontendReady) {
    Write-Host "ERROR: Frontend did not become ready in time" -ForegroundColor Red
    docker-compose logs frontend
    docker-compose down
    exit 1
}

Write-Host "Running integration tests..." -ForegroundColor Green
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if we're in a virtual environment, if not, try to use backend's venv
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path "backend\venv\Scripts\Activate.ps1") {
        & "backend\venv\Scripts\Activate.ps1"
    }
}

python -m pytest tests/ -v -m integration --tb=short

$testExitCode = $LASTEXITCODE

Write-Host "Stopping services..." -ForegroundColor Yellow
docker-compose down

exit $testExitCode

