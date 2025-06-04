#
# Kor'tana Environment Diagnostics
#
# This script runs all diagnostic tests and collects the results
#

Write-Host "===== Kor'tana Environment Diagnostics =====" -ForegroundColor Blue
Write-Host "Running diagnostic tests and collecting results..."

# Create a diagnostics directory with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$diagDir = "diagnostics_$timestamp"
New-Item -ItemType Directory -Path $diagDir -Force | Out-Null

Write-Host "Creating diagnostics directory: $diagDir"

# Step 1: Run basic execution test
Write-Host ""
Write-Host "===== Running basic execution test =====" -ForegroundColor Yellow
Write-Host ""
python test_exec.py > "$diagDir\exec_result.txt"
Get-Content "$diagDir\exec_result.txt"

# Step 2: Run environment diagnostics
Write-Host ""
Write-Host "===== Running environment diagnostics =====" -ForegroundColor Yellow
Write-Host ""
python scripts\diagnose_environment.py > "$diagDir\diag_env_result.txt"
Get-Content "$diagDir\diag_env_result.txt" | Select-Object -First 30
Write-Host "... (output truncated, see full results in file)"

# Step 3: Run config loading test
Write-Host ""
Write-Host "===== Running config loading test =====" -ForegroundColor Yellow
Write-Host ""
python scripts\test_config_loading.py > "$diagDir\config_load_result.txt"
Write-Host "Results saved to $diagDir\config_load_result.txt"

# Step 4: Run integrated test
Write-Host ""
Write-Host "===== Running integrated test =====" -ForegroundColor Yellow
Write-Host ""
python test_config_integrated.py > "$diagDir\integrated_result.txt"
Get-Content "$diagDir\integrated_result.txt" | Select-Object -First 30
Write-Host "... (output truncated, see full results in file)"

# Step 5: Run audit collection
Write-Host ""
Write-Host "===== Running audit collection =====" -ForegroundColor Yellow
Write-Host ""
python scripts\collect_audit_artifacts_fixed.py
Copy-Item -Path "audit_log.txt" -Destination "$diagDir\audit_log.txt"

# Create a summary file
Write-Host ""
Write-Host "===== Creating summary =====" -ForegroundColor Yellow
Write-Host ""

$summary = @"
Kor'tana Diagnostic Summary
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

All diagnostic results are available in the $diagDir directory.

Files included:
- exec_result.txt: Basic Python execution environment information
- diag_env_result.txt: Detailed environment diagnostic information
- config_load_result.txt: Configuration loading test results
- integrated_result.txt: Integrated environment and config test
- audit_log.txt: Full audit results

IMPORTANT: Do not proceed with config code or environment refactors
until sanctuary (matt) has reviewed and confirmed a stable,
reproducible environment based on these diagnostic outputs.
"@

$summary | Out-File -FilePath "$diagDir\summary.txt"

Write-Host ""
Write-Host "===== Diagnostics Complete =====" -ForegroundColor Green
Write-Host ""
Write-Host "All diagnostic results have been saved to the $diagDir directory." -ForegroundColor Green
Write-Host "Please review the files and share them with sanctuary (matt) for analysis." -ForegroundColor Yellow
Write-Host "No changes to configuration code should be made until after review." -ForegroundColor Yellow
