#
# Setup Test Environment for Kor'tana
#
# This script creates a fresh virtual environment and runs diagnostic tests
#

# Test environment name
$TestEnv = ".kortana_test_env"

Write-Host "Setting up a fresh test environment for Kor'tana..." -ForegroundColor Blue

# Create a clean test directory
if (Test-Path $TestEnv) {
    Write-Host "Removing existing test environment..."
    Remove-Item -Path $TestEnv -Recurse -Force
}

Write-Host "Creating new test environment..."
python -m venv $TestEnv

# Activate virtual environment
Write-Host "Activating test environment..."
$ActivateScript = Join-Path -Path $TestEnv -ChildPath "Scripts\Activate.ps1"
& $ActivateScript

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install pyyaml pydantic python-dotenv

# Install package in development mode
Write-Host "Installing package in development mode..." -ForegroundColor Green
pip install -e .

Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host ""

# Run diagnostic scripts
Write-Host "Running diagnostic scripts..." -ForegroundColor Blue
Write-Host ""
Write-Host "===== ENVIRONMENT DIAGNOSTIC =====" -ForegroundColor Yellow
python scripts\diagnose_environment.py > env_diagnostic.log
Get-Content env_diagnostic.log

Write-Host ""
Write-Host "===== CONFIG LOADING TEST =====" -ForegroundColor Yellow
python scripts\test_config_loading.py > config_test.log
Get-Content config_test.log

Write-Host ""
Write-Host "===== INTEGRATED TEST =====" -ForegroundColor Yellow
python test_config_integrated.py

Write-Host ""
Write-Host "Diagnostic complete!" -ForegroundColor Green
Write-Host "Results saved to env_diagnostic.log, config_test.log, and config_test_*.txt" -ForegroundColor Green

# Keep the environment active for further testing
Write-Host ""
Write-Host "Test environment is active. Run 'deactivate' when finished." -ForegroundColor Yellow
