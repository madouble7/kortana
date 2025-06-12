# Run Kor'tana API server for LobeChat integration
Write-Host "Starting Kor'tana API server..." -ForegroundColor Green
Write-Host ""
Write-Host "API will be available at http://localhost:8000" -ForegroundColor Cyan
Write-Host "LobeChat adapter at http://localhost:8000/api/lobe/chat" -ForegroundColor Cyan
Write-Host ""

# Ensure Python environment is activated
& "$PSScriptRoot\venv311\Scripts\Activate.ps1"

# Run the application
Push-Location "$PSScriptRoot\src"
python -m uvicorn kortana.main:app --reload --port 8000 --host 0.0.0.0
Pop-Location

Write-Host "API server stopped." -ForegroundColor Yellow
