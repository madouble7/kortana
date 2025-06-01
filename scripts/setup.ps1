# Check if PowerShell execution policy allows script execution
$policy = Get-ExecutionPolicy
Write-Host "Current execution policy: $policy"
if ($policy -eq "Restricted") {
    Write-Host "Setting execution policy to RemoteSigned for current process..."
    Set-ExecutionPolicy RemoteSigned -Scope Process -Force
}

# Navigate to project root
Set-Location (Split-Path $MyInvocation.MyCommand.Path)

# Clean up old virtual environment
if (Test-Path "venv311") {
    Write-Host "Removing existing virtual environment..."
    Remove-Item -Path "venv311" -Recurse -Force
}

# Create fresh virtual environment
Write-Host "Creating new virtual environment..."
python -m venv venv311

# Verify venv creation
if (-not (Test-Path "venv311\Scripts\Activate.ps1")) {
    Write-Host "Error: Virtual environment creation failed!" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\venv311\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing required packages..."
pip install google-generativeai==0.8.5 python-dotenv==1.0.1

Write-Host "Setup complete. Your virtual environment is now active." -ForegroundColor Green
Write-Host "You can now run: python test_genai.py"
