# Fix-And-Run.ps1
# Fixes permissions and runs Kor'tana

Write-Host "===== Kor'tana Setup and Run =====" -ForegroundColor Cyan
Write-Host ""

# Check for required packages
Write-Host "Checking required packages..." -ForegroundColor Yellow
$packages = @("pyyaml", "apscheduler", "pydantic")
foreach ($package in $packages) {
    try {
        python -c "import $package"
        Write-Host "✓ $package is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ $package is missing, installing..." -ForegroundColor Red
        python -m pip install $package
    }
}

# Fix permissions and create required files
Write-Host "`nFixing permissions and creating required files..." -ForegroundColor Yellow
python src/fix_permissions.py

# Run the application
Write-Host "`nStarting Kor'tana..." -ForegroundColor Yellow
Write-Host "`nTo exit, type 'bye' or press Ctrl+C`n" -ForegroundColor Magenta

# Run Kor'tana
python -m src.kortana.core.brain

Write-Host "`n===== Run Complete =====" -ForegroundColor Cyan
Write-Host ""
