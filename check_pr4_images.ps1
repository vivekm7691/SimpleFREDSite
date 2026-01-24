# PowerShell script to diagnose PR-4 Docker image issues
# This script helps identify what commit the PR-4 tag currently points to

Write-Host "=== PR-4 Docker Image Diagnostic Script ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REGISTRY = "ghcr.io"
$REPO = "vivekm7691/simplefredsite"
$BACKEND_IMAGE = "${REGISTRY}/${REPO}/fred-backend"
$FRONTEND_IMAGE = "${REGISTRY}/${REPO}/fred-frontend"
$TAG = "pr-4"

Write-Host "Checking local Docker images..." -ForegroundColor Yellow
Write-Host ""

# Check if PR-4 images exist locally
Write-Host "1. Local PR-4 Images:" -ForegroundColor Green
$backendLocal = docker images "${BACKEND_IMAGE}:${TAG}" --format "{{.Repository}}:{{.Tag}}"
$frontendLocal = docker images "${FRONTEND_IMAGE}:${TAG}" --format "{{.Repository}}:{{.Tag}}"

if ($backendLocal) {
    Write-Host "   Backend: $backendLocal" -ForegroundColor White
    docker images "${BACKEND_IMAGE}:${TAG}" --format "   Created: {{.CreatedAt}} | Size: {{.Size}}"
} else {
    Write-Host "   Backend: Not found locally" -ForegroundColor Red
}

if ($frontendLocal) {
    Write-Host "   Frontend: $frontendLocal" -ForegroundColor White
    docker images "${FRONTEND_IMAGE}:${TAG}" --format "   Created: {{.CreatedAt}} | Size: {{.Size}}"
} else {
    Write-Host "   Frontend: Not found locally" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Inspecting image metadata..." -ForegroundColor Green

if ($backendLocal) {
    Write-Host "   Backend Image Details:" -ForegroundColor Yellow
    $backendInspect = docker inspect "${BACKEND_IMAGE}:${TAG}" 2>$null
    if ($backendInspect) {
        # Try to extract commit SHA from labels
        $labels = docker inspect "${BACKEND_IMAGE}:${TAG}" --format '{{range .Config.Labels}}{{println .}}{{end}}' 2>$null
        if ($labels) {
            Write-Host "   Labels:" -ForegroundColor Cyan
            $labels | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
        }
        
        # Show creation date
        $created = docker inspect "${BACKEND_IMAGE}:${TAG}" --format '{{.Created}}' 2>$null
        if ($created) {
            Write-Host "   Created: $created" -ForegroundColor Cyan
        }
    }
}

if ($frontendLocal) {
    Write-Host "   Frontend Image Details:" -ForegroundColor Yellow
    $frontendInspect = docker inspect "${FRONTEND_IMAGE}:${TAG}" 2>$null
    if ($frontendInspect) {
        $labels = docker inspect "${FRONTEND_IMAGE}:${TAG}" --format '{{range .Config.Labels}}{{println .}}{{end}}' 2>$null
        if ($labels) {
            Write-Host "   Labels:" -ForegroundColor Cyan
            $labels | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
        }
        
        $created = docker inspect "${FRONTEND_IMAGE}:${TAG}" --format '{{.Created}}' 2>$null
        if ($created) {
            Write-Host "   Created: $created" -ForegroundColor Cyan
        }
    }
}

Write-Host ""
Write-Host "3. Recommendations:" -ForegroundColor Green
Write-Host ""
Write-Host "   If PR-4 images don't have your expected changes:" -ForegroundColor Yellow
Write-Host "   1. The PR-4 tag may have been overwritten by a new build" -ForegroundColor White
Write-Host "   2. Check GitHub Actions to find the commit SHA from yesterday" -ForegroundColor White
Write-Host "   3. Pull images using commit SHA instead: docker pull ${BACKEND_IMAGE}:<commit-sha>" -ForegroundColor White
Write-Host ""
Write-Host "   To force pull fresh PR-4 images (may be different from yesterday):" -ForegroundColor Yellow
Write-Host "   docker pull --no-cache ${BACKEND_IMAGE}:${TAG}" -ForegroundColor Cyan
Write-Host "   docker pull --no-cache ${FRONTEND_IMAGE}:${TAG}" -ForegroundColor Cyan
Write-Host ""
Write-Host "   To remove local cached images:" -ForegroundColor Yellow
Write-Host "   docker rmi ${BACKEND_IMAGE}:${TAG}" -ForegroundColor Cyan
Write-Host "   docker rmi ${FRONTEND_IMAGE}:${TAG}" -ForegroundColor Cyan
Write-Host ""

# Check if user wants to pull fresh images
$response = Read-Host "Do you want to pull fresh PR-4 images now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Pulling fresh PR-4 images..." -ForegroundColor Yellow
    
    Write-Host "Pulling backend..." -ForegroundColor Cyan
    docker pull "${BACKEND_IMAGE}:${TAG}"
    
    Write-Host "Pulling frontend..." -ForegroundColor Cyan
    docker pull "${FRONTEND_IMAGE}:${TAG}"
    
    Write-Host ""
    Write-Host "Done! Fresh images pulled." -ForegroundColor Green
}

Write-Host ""
Write-Host "For more information, see: DIAGNOSE_DOCKER_IMAGES.md" -ForegroundColor Cyan




