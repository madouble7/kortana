# Kortana Audit Check Script
# This script generates the required audit files

# Ensure we're using the virtual environment's Python
Write-Host "Activating virtual environment..." -ForegroundColor Green
if (Test-Path 'C:\kortana\venv311\Scripts\Activate.ps1') {
    # Use venv311 if it exists
    & 'C:\kortana\venv311\Scripts\Activate.ps1'
} elseif (Test-Path 'C:\kortana\.venv\Scripts\Activate.ps1') {
    # Otherwise use .venv if it exists
    & 'C:\kortana\.venv\Scripts\Activate.ps1'
} else {
    Write-Host "Virtual environment not found! Some tests may fail." -ForegroundColor Red
}

# 1. Import check - manual approach to debug import issues
Write-Host "Running import check..." -ForegroundColor Green
$importCheck = python -c "import sys; sys.path.insert(0, 'C:/kortana/src'); import kortana; print('kortana imported from:', kortana.__file__); import pkg_resources; print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])" 2>&1
if ($LASTEXITCODE -eq 0) {
    $importCheck | Out-File -FilePath "import_check.txt" -Encoding utf8
    Write-Host "Import check successful!" -ForegroundColor Green
} else {
    "Error importing kortana module. See below for details:

$importCheck" | Out-File -FilePath "import_check.txt" -Encoding utf8
    Write-Host "Import check failed! See import_check.txt for details." -ForegroundColor Red
}

# 2. Run pytest with coverage - try using Python module path
Write-Host "Running pytest with coverage..." -ForegroundColor Green
try {
    python -m pytest -q --cov=kortana | Out-File -FilePath "pytest_output.txt" -Encoding utf8
    Write-Host "Pytest run successful!" -ForegroundColor Green
} catch {
    "Error running pytest. Details:

$_" | Out-File -FilePath "pytest_output.txt" -Encoding utf8
    Write-Host "Pytest run failed! See pytest_output.txt for details." -ForegroundColor Red
}

# 3. Test config loading
Write-Host "Testing configuration loading..." -ForegroundColor Green
$configCheck = python -c "import sys; sys.path.insert(0, 'C:/kortana'); from config import load_config; print(load_config().model_dump())" 2>&1
if ($LASTEXITCODE -eq 0) {
    $configCheck | Out-File -FilePath "config_check.txt" -Encoding utf8
    Write-Host "Config check successful!" -ForegroundColor Green
} else {
    "Error loading configuration. See below for details:

$configCheck" | Out-File -FilePath "config_check.txt" -Encoding utf8
    Write-Host "Config check failed! See config_check.txt for details." -ForegroundColor Red
}

# 4. Check for stray yaml loads
Write-Host "Checking for stray YAML reads..." -ForegroundColor Green
$yamlGrep = Get-ChildItem -Recurse src\kortana -Filter *.py | Select-String -Pattern 'yaml\.safe_load\(' , '\.yaml[\"''\"]'
if ($yamlGrep) {
    $yamlGrep | Out-File -FilePath "yaml_grep.txt" -Encoding utf8
} else {
    "No stray YAML reads found. Great!" | Out-File -FilePath "yaml_grep.txt" -Encoding utf8
}
Write-Host "YAML check complete!" -ForegroundColor Green

# 5. Verify all files were created
Write-Host "
Verifying generated files:" -ForegroundColor Green
Get-Item import_check.txt, pytest_output.txt, config_check.txt, yaml_grep.txt | ForEach-Object {
    Write-Host "$($_.Name): $($_.Length) bytes" -ForegroundColor Cyan
}

Write-Host "
Audit checks complete!" -ForegroundColor Green
Write-Host "Please provide these files to the auditor." -ForegroundColor Green
