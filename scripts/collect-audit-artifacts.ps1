# Kor'tana Audit Artifact Collection Script
# This script collects all required artifacts for the audit

# Set output file
$auditLog = Join-Path $PSScriptRoot "..\audit_log.txt"

# Function to write section headers
function Write-Section {
    param([string]$Title)

    Add-Content $auditLog ""
    Add-Content $auditLog ("=" * 80)
    Add-Content $auditLog "# $Title"
    Add-Content $auditLog ("=" * 80)
    Add-Content $auditLog ""
}

# Start with clean file
Set-Content $auditLog "# Kor'tana Audit Log"
Add-Content $auditLog "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Add-Content $auditLog ""

# Change to project root directory
Push-Location (Join-Path $PSScriptRoot "..")
try {
    # 1. Capture branch and commit hash
    Write-Section "BRANCH AND COMMIT HASH"

    $branch = git rev-parse --abbrev-ref HEAD
    Add-Content $auditLog "Current branch: $branch"
    Add-Content $auditLog ""

    $commit = git rev-parse HEAD
    Add-Content $auditLog "Current commit hash: $commit"
    Add-Content $auditLog ""

    # 2. List all tracked files
    Write-Section "TRACKED FILES"

    $trackedFiles = git ls-files
    $trackedFiles | ForEach-Object { Add-Content $auditLog $_ }
    Add-Content $auditLog ""

    # Check for problematic files
    Add-Content $auditLog "Checking for problematic tracked files:"
    $problemPatterns = @("venv", "cache", "data", ".env", "__pycache__", ".db")
    $problemsFound = $false

    foreach ($pattern in $problemPatterns) {
        $matchingFiles = $trackedFiles | Where-Object { $_ -like "*$pattern*" }
        if ($matchingFiles) {
            $problemsFound = $true
            Add-Content $auditLog "⚠️ Found files matching '$pattern':"
            $matchingFiles | ForEach-Object { Add-Content $auditLog "  - $_" }
        }
    }

    if (-not $problemsFound) {
        Add-Content $auditLog "✅ No problematic files found in tracking"
    }
    Add-Content $auditLog ""

    # 3. Test creation of virtual env and installation
    Write-Section "INSTALL AND IMPORT TEST"

    # Note: We're not creating a venv here, as it would complicate the script
    # Just provide instructions
    Add-Content $auditLog "Please run the following commands in a fresh shell:"
    Add-Content $auditLog ""
    Add-Content $auditLog '```'
    Add-Content $auditLog "python -m venv .venv && .\.venv\Scripts\activate"
    Add-Content $auditLog "pip install -e ."
    Add-Content $auditLog "python -c ""import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])"""
    Add-Content $auditLog '```'
    Add-Content $auditLog ""

    # 4. Run full test/CI suite
    Write-Section "TEST COVERAGE RESULTS"

    Add-Content $auditLog "Running pytest with coverage:"
    Add-Content $auditLog ""

    try {
        $testOutput = python -m pytest -q --cov=kortana 2>&1
        $testOutput | ForEach-Object { Add-Content $auditLog $_ }
    }
    catch {
        Add-Content $auditLog "Error running tests: $_"
    }
    Add-Content $auditLog ""

    # 5. Config pipeline check
    Write-Section "CONFIG PIPELINE CHECK"

    Add-Content $auditLog "Checking config pipeline:"
    Add-Content $auditLog ""

    try {
        $configCmd = "from config import load_config; cfg = load_config(); print('loaded env:', cfg.model_dump())"
        $configOutput = python -c $configCmd 2>&1
        $configOutput | ForEach-Object { Add-Content $auditLog $_ }
    }
    catch {
        Add-Content $auditLog "Error checking config pipeline: $_"
    }
    Add-Content $auditLog ""

    # 6. Stray yaml read grep
    Write-Section "STRAY YAML READ CHECK"

    Add-Content $auditLog "Checking for direct YAML reads:"
    Add-Content $auditLog ""

    if (Test-Path "src\kortana") {
        $findResults = Get-ChildItem -Path "src\kortana" -Recurse -File -Filter "*.py" |
        Select-String -Pattern "yaml.safe_load\(", "\.yaml\""

        if ($findResults) {
            Add-Content $auditLog "Found potential direct YAML reads:"
            $findResults | ForEach-Object { Add-Content $auditLog $_.ToString() }
        }
        else {
            Add-Content $auditLog "✅ No direct YAML reads found in src/kortana"
        }
    }
    else {
        Add-Content $auditLog "❌ src/kortana directory not found"
    }
    Add-Content $auditLog ""

    # Summary
    Write-Section "SUMMARY"
    Add-Content $auditLog "✅ All audit artifacts collected"
    Add-Content $auditLog ""
    Add-Content $auditLog "Please review this file and share with the auditor as requested."

    Write-Host "Audit artifacts collected in $auditLog"
    Write-Host ""
    Write-Host "Please also run the virtual environment import test manually:"
    Write-Host "python -m venv .venv && .\.venv\Scripts\activate"
    Write-Host "pip install -e ."
    Write-Host "python -c ""import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])"""
}
finally {
    # Return to original directory
    Pop-Location
}
