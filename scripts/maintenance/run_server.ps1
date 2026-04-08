$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendRoot = Join-Path $repoRoot "backend"
$venvPython = Join-Path $repoRoot "venv\\Scripts\\python.exe"

$env:PYTHONPATH = $backendRoot

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python not found at $venvPython"
}

Push-Location $backendRoot
try {
    & $venvPython -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000
} finally {
    Pop-Location
}
