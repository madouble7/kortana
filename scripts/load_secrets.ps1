param(
[string]$SecretId = "kortana/dev",
[string]$Profile = $env:AWS_PROFILE ?? "default"
)

$json = aws --profile $Profile secretsmanager get-secret-value --secret-id $SecretId --query SecretString --output text 2>$null
if (-not $json) { Write-Error "Failed to fetch secret: $SecretId"; exit 1 }

$secrets = $json | ConvertFrom-Json

foreach ($prop in $secrets.PSObject.Properties) {
  [Environment]::SetEnvironmentVariable($prop.Name, $prop.Value, "Process")
  Write-Host "Loaded: $($prop.Name)"
}

$keys = $secrets.PSObject.Properties.Name -join ", "
Write-Host "Secrets loaded from $SecretId (keys: $keys) using profile $Profile"

# Usage: .\scripts\load_secrets.ps1 kortana/dev
# Loads env vars; verify with: node -e "console.log(process.env.OPENROUTER_API_KEY?.substring(0,6) + '...')"
