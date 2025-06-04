# Run-Kortana.ps1 - Batch 1
# PowerShell script to run Kor'tana

Write-Host "===== Kor'tana: Batch 1 =====" -ForegroundColor Cyan
Write-Host ""

# Set PYTHONPATH environment variable to include the project root
$env:PYTHONPATH = $PSScriptRoot

# Run the setup and brain module
python scripts/setup_and_run_batch1.py

Write-Host ""
Write-Host "===== Run Complete =====" -ForegroundColor Cyan
Write-Host ""

Read-Host -Prompt "Press Enter to continue"
