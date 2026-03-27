# TrustLayer ID - Test Runner Script (PowerShell)
# Runs all unit and integration tests for backend and frontend

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrustLayer ID - Test Suite Runner" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Backend Tests
Write-Host "Running Backend Tests..." -ForegroundColor Yellow
Write-Host ""

Set-Location backend-merged

Write-Host "Installing backend test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock

Write-Host ""
Write-Host "Running backend unit tests..."
pytest tests/unit -v --cov=app --cov-report=term-missing --cov-report=html:../coverage/backend

$BackendExitCode = $LASTEXITCODE

if ($BackendExitCode -eq 0) {
    Write-Host "✓ Backend unit tests passed" -ForegroundColor Green
} else {
    Write-Host "✗ Backend unit tests failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Running backend integration tests..."
pytest tests/integration -v

$BackendIntegrationExitCode = $LASTEXITCODE

if ($BackendIntegrationExitCode -eq 0) {
    Write-Host "✓ Backend integration tests passed" -ForegroundColor Green
} else {
    Write-Host "✗ Backend integration tests failed" -ForegroundColor Red
}

Set-Location ..

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

# Frontend Tests
Write-Host "Running Frontend Tests..." -ForegroundColor Yellow
Write-Host ""

Set-Location frontend

Write-Host "Installing frontend test dependencies..."
npm install --silent

Write-Host ""
Write-Host "Running frontend tests..."
npm test -- --coverage --reporter=verbose

$FrontendExitCode = $LASTEXITCODE

if ($FrontendExitCode -eq 0) {
    Write-Host "✓ Frontend tests passed" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend tests failed" -ForegroundColor Red
}

Set-Location ..

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if ($BackendExitCode -eq 0) {
    Write-Host "✓ Backend Unit Tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Backend Unit Tests: FAILED" -ForegroundColor Red
}

if ($BackendIntegrationExitCode -eq 0) {
    Write-Host "✓ Backend Integration Tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Backend Integration Tests: FAILED" -ForegroundColor Red
}

if ($FrontendExitCode -eq 0) {
    Write-Host "✓ Frontend Tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend Tests: FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Coverage reports generated:"
Write-Host "  - Backend: coverage/backend/index.html"
Write-Host "  - Frontend: frontend/coverage/index.html"
Write-Host ""

# Exit with error if any tests failed
if (($BackendExitCode -ne 0) -or ($BackendIntegrationExitCode -ne 0) -or ($FrontendExitCode -ne 0)) {
    Write-Host "Some tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "All tests passed successfully!" -ForegroundColor Green
exit 0
