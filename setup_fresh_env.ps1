# PowerShell script to setup environment
Set-Location c:\kortana

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Removing old venv if it exists..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if (Test-Path ".kortana_config_test_env") {
    Remove-Item -Recurse -Force ".kortana_config_test_env" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Creating fresh virtual environment..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

& "C:\Program Files\Python311\python.exe" -m venv .kortana_config_test_env
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create venv" -ForegroundColor Red
    exit 1
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Upgrading pip..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

& ".\.kortana_config_test_env\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Installing dependencies..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

& ".\.kortana_config_test_env\Scripts\pip.exe" install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Installing test dependencies..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

& ".\.kortana_config_test_env\Scripts\pip.exe" install pytest pytest-asyncio pytest-mock
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install test dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "======================================" -ForegroundColor Green
Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
