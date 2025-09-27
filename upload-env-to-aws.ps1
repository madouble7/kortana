<#
    upload-env-to-aws.ps1
    Hardened PowerShell helper to sync a local .env file into AWS Secrets Manager.
    Features:
        - Environment prefix (env-scoped secrets: e.g. kortana/prod/OPENAI_API_KEY)
        - Idempotent upsert (create or update existing)
        - Optional single-bundle export (store whole file as one secret)
        - Optional KMS CMK usage
        - Consistent tagging (Project, Env, ManagedBy)
        - Basic format warnings (OpenAI, Stripe, Twilio, Groq)
        - Skips blank/comment lines; tolerates quoted values
        - Refuses empty prefix to avoid root namespace pollution
    Usage Examples:
        pwsh .\upload-env-to-aws.ps1 -EnvFile C:\Users\me\.env -Prefix kortana/prod
        pwsh .\upload-env-to-aws.ps1 -EnvFile .env -Prefix kortana/dev -Profile kortana -Region us-east-2
        # Store entire file as one secret:
        pwsh .\upload-env-to-aws.ps1 -BundleSecretName kortana/prod/env-file
    NOTE: Key casing is preserved (no forced lowercase) to align with existing loader expectations.
#>
param(
    [string]$EnvFile = "$HOME/.env",
    [string]$Prefix = "kortana/prod",
    [string]$Profile = "kortana",
    [string]$Region = "us-east-2",
    [string]$KmsKeyId = "",             # Optional CMK ARN or ID
    [switch]$DryRun,
    [string]$BundleSecretName = ""       # If provided, store entire file as one secret and exit
)

Write-Host "🔐 Kor'tana .env → AWS Secrets Manager Sync" -ForegroundColor Green
Write-Host "📁 Env file: $EnvFile" -ForegroundColor Yellow
Write-Host "🪪 AWS Profile: $Profile" -ForegroundColor Yellow
Write-Host "� Region: $Region" -ForegroundColor Yellow
Write-Host "🏷️  Prefix: $Prefix" -ForegroundColor Yellow
if ($KmsKeyId) { Write-Host "🔐 Using KMS Key: $KmsKeyId" -ForegroundColor Yellow }
if ($DryRun) { Write-Host "🚧 Dry-run mode (no changes will be made)." -ForegroundColor Cyan }
Write-Host ""

if (-not (Test-Path $EnvFile)) { Write-Host "❌ Env file not found: $EnvFile" -ForegroundColor Red; exit 1 }
if ([string]::IsNullOrWhiteSpace($Prefix)) { Write-Host "❌ Prefix is empty. Aborting." -ForegroundColor Red; exit 1 }

# Light namespace format hint
if ($Prefix -notmatch '^[a-z0-9-]+/[a-z0-9-]+$') { Write-Host "⚠️  Prefix '$Prefix' does not match pattern namespace/env (e.g. kortana/prod)." -ForegroundColor DarkYellow }

$envName = ($Prefix -split '/')[1]
$tags = @(
    @{ Key = 'Project'; Value = 'kortana' },
    @{ Key = 'Env';     Value = $envName },
    @{ Key = 'ManagedBy'; Value = 'upload-script' }
)

function Convert-TagsJson {
    param($TagArray)
    return ($TagArray | ConvertTo-Json -Compress)
}

function Set-Secret {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description = "Kor'tana secret"
    )
    $kmsArgs = @()
    if ($KmsKeyId) { $kmsArgs += @('--kms-key-id', $KmsKeyId) }
    $exists = $false
    try {
        aws secretsmanager describe-secret --secret-id $Name --profile $Profile --region $Region | Out-Null
        $exists = $true
    } catch { $exists = $false }

    if ($DryRun) {
        Write-Host "[dry-run] $($exists ? 'Update' : 'Create') $Name" -ForegroundColor Cyan
        return
    }

    if ($exists) {
        aws secretsmanager put-secret-value --secret-id $Name --secret-string $Value --profile $Profile --region $Region | Out-Null
        # Re-tag to ensure consistency (ignore failures)
        try { aws secretsmanager tag-resource --secret-id $Name --tags (Convert-TagsJson $tags) --profile $Profile --region $Region | Out-Null } catch { }
        if ($KmsKeyId) {
            try {
                $currentKms = aws secretsmanager describe-secret --secret-id $Name --query 'KmsKeyId' --output text --profile $Profile --region $Region 2>$null
                if ($currentKms -and $currentKms -ne $KmsKeyId -and $currentKms -ne 'None') {
                    aws secretsmanager update-secret --secret-id $Name --kms-key-id $KmsKeyId --profile $Profile --region $Region | Out-Null
                }
            } catch { }
        }
        Write-Host "� Updated: $Name" -ForegroundColor Green
    } else {
        aws secretsmanager create-secret --name $Name --secret-string $Value --description $Description --tags (Convert-TagsJson $tags) --profile $Profile --region $Region @kmsArgs | Out-Null
        Write-Host "✅ Created: $Name" -ForegroundColor Green
    }
}

if ($BundleSecretName) {
    Write-Host "📦 Bundling entire file into single secret: $BundleSecretName" -ForegroundColor Cyan
    $raw = Get-Content $EnvFile -Raw
    Set-Secret -Name $BundleSecretName -Value $raw -Description "Kor'tana env file bundle"
    Write-Host "🎉 Completed bundle upload." -ForegroundColor Green
    exit 0
}

# Basic pattern warnings function
function Warn-Formats {
    param($Key,$Value)
    switch ($Key) {
        'OPENAI_API_KEY' { if ($Value -notmatch '^sk-') { Write-Host "⚠️  $Key value does not start with sk-" -ForegroundColor DarkYellow } }
        'STRIPE_SECRET_KEY' { if ($Value -notmatch '^sk_') { Write-Host "⚠️  $Key value does not start with sk_" -ForegroundColor DarkYellow } }
        'TWILIO_ACCOUNT_SID' { if ($Value -notmatch '^AC') { Write-Host "⚠️  $Key value does not start with AC" -ForegroundColor DarkYellow } }
        'GROQ_API_KEY' { if ($Value -notmatch '^gsk_') { Write-Host "⚠️  $Key value does not start with gsk_" -ForegroundColor DarkYellow } }
    }
}

$lineNumber = 0
Get-Content $EnvFile | ForEach-Object {
    $lineNumber++
    $rawLine = $_
    $line = $rawLine.Trim()
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { return }
    # Skip export statements (bash style)
    if ($line -match '^(export )') { $line = $line.Substring(7) }
    # Parse KEY=VALUE (allow empty value but skip if empty after trim)
    if ($line -notmatch '^[A-Za-z_][A-Za-z0-9_]*=') { Write-Host "ℹ️  Skipping non-assignment line $lineNumber" -ForegroundColor DarkGray; return }
    $eqIndex = $line.IndexOf('=')
    if ($eqIndex -lt 1) { return }
    $key = $line.Substring(0,$eqIndex).Trim()
    $value = $line.Substring($eqIndex+1).Trim()

    # Remove optional surrounding quotes (single or double)
    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1,$value.Length-2)
    }
    if ([string]::IsNullOrWhiteSpace($value)) { Write-Host "⚠️  Skipping $key (empty value)" -ForegroundColor DarkYellow; return }

    Warn-Formats -Key $key -Value $value

    $secretName = "$Prefix/$key"
    Set-Secret -Name $secretName -Value $value -Description "Kor'tana $envName: $key"
    Start-Sleep -Milliseconds 150
}

Write-Host ""; Write-Host "🎉 Sync complete." -ForegroundColor Green
Write-Host "🔍 Verify in console: https://console.aws.amazon.com/secretsmanager/home?region=$Region#/listSecrets" -ForegroundColor Cyan
