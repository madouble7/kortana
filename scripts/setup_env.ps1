# Setup environment variables for Kor'tana
param(
    [Parameter(Mandatory=$true)]
    [string]$GoogleApiKey
)

# Set environment variables
Write-Host "Setting GOOGLE_API_KEY environment variable..."
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $GoogleApiKey, [System.EnvironmentVariableTarget]::User)

# Verify the variable was set
$verifyKey = [System.Environment]::GetEnvironmentVariable("GOOGLE_API_KEY", [System.EnvironmentVariableTarget]::User)
if ($verifyKey -eq $GoogleApiKey) {
    Write-Host "[SUCCESS] GOOGLE_API_KEY environment variable set successfully"
} else {
    Write-Host "[ERROR] Failed to set GOOGLE_API_KEY environment variable"
    exit 1
}

Write-Host "Environment setup complete. Please restart your terminal for changes to take effect."
