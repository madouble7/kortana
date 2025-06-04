# Install-Fixed-Brain.ps1
# Installs the fixed brain.py file

Write-Host "===== Installing Fixed Brain.py =====" -ForegroundColor Cyan
Write-Host ""

# Define paths
$fixedPath = "src/fixed_brain.py"
$targetPath = "src/kortana/core/brain.py"
$backupPath = "src/kortana/core/brain.py.bak"

# Check if fixed file exists
if (-not (Test-Path $fixedPath)) {
    Write-Host "Error: Fixed brain file not found at $fixedPath" -ForegroundColor Red
    exit 1
}

# Create backup if target exists
if (Test-Path $targetPath) {
    Write-Host "Creating backup of original file..." -ForegroundColor Yellow
    Copy-Item -Path $targetPath -Destination $backupPath -Force
    Write-Host "Backup created at $backupPath" -ForegroundColor Green
}

# Copy fixed file to target location
try {
    Write-Host "Installing fixed brain.py..." -ForegroundColor Yellow
    Copy-Item -Path $fixedPath -Destination $targetPath -Force
    Write-Host "Fixed brain.py successfully installed at $targetPath" -ForegroundColor Green
}
catch {
    Write-Host "Error installing fixed file: $_" -ForegroundColor Red
    exit 1
}

# Success message
Write-Host "`nInstallation complete!" -ForegroundColor Cyan
Write-Host "You can now run: python -m src.kortana.core.brain" -ForegroundColor Magenta
Write-Host ""
