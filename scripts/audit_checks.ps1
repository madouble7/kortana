# Audit Checks Script for Kortana
Write-Host "Running audit checks for Kortana..." -ForegroundColor Green

# First, upgrade pip
Write-Host "
Upgrading pip..." -ForegroundColor Yellow
python -m pip install -U pip

# Change to parent directory to avoid import conflicts
Push-Location ..
Write-Host "
Running import check..." -ForegroundColor Yellow
@'
import pathlib, pkg_resources, kortana
print("kortana imported from:", pathlib.Path(kortana.__file__).resolve())
print("console scripts:", [e.name for e in pkg_resources.iter_entry_points("console_scripts") if "kortana" in e.name])
'@ | python > C:\kortana\import_check.txt

Write-Host "
Installing pytest and coverage..." -ForegroundColor Yellow
pip install pytest coverage[toml]

Write-Host "
Running tests with coverage..." -ForegroundColor Yellow
pytest -q --cov=kortana C:\kortana > C:\kortana\pytest_output.txt

Write-Host "
Testing config pipeline..." -ForegroundColor Yellow
@'
from config import load_config
print(load_config().model_dump())
'@ | python > C:\kortana\config_check.txt

# Return to original directory
Pop-Location

Write-Host "
Checking for stray YAML reads..." -ForegroundColor Yellow
Get-ChildItem -Recurse src\kortana -Filter *.py | 
  Select-String -Pattern 'yaml\.safe_load\(' , '\.yaml[\"''\"]' | 
  Set-Content yaml_grep.txt

Write-Host "
Verifying generated files:" -ForegroundColor Green
dir import_check.txt, pytest_output.txt, config_check.txt, yaml_grep.txt

Write-Host "
Audit checks complete!" -ForegroundColor Green
Write-Host "Please provide these files to the auditor." -ForegroundColor Green
