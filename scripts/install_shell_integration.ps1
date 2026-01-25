<#
PowerShell helper to install VS Code shell integration into the current user's PowerShell profile.
Run in an elevated or normal PowerShell session: `.	ools\install_shell_integration.ps1` or dot-source it.
#>

$ErrorActionPreference = 'Stop'

function Get-CodePath {
    $codeCmd = Get-Command code -ErrorAction SilentlyContinue
    if (-not $codeCmd) {
        Write-Error "'code' is not on PATH. Open VS Code, run 'Shell Command: Install 'code' command in PATH' from the Command Palette, then re-run this script."
        exit 2
    }
    return (code --locate-shell-integration-path pwsh 2>$null)
}

$path = Get-CodePath
if (-not $path) {
    Write-Error "Could not locate shell integration path for PowerShell. Ensure VS Code supports shell integration on this version.";
    exit 1
}

$profilePath = $PROFILE
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$sourceLine = "if ($env:TERM_PROGRAM -eq 'vscode') { . \"$path\" }"

# ensure idempotent insertion
$contents = Get-Content -Raw -Path $profilePath
if ($contents -notmatch [regex]::Escape($sourceLine)) {
    Add-Content -Path $profilePath -Value "`n# VS Code Shell Integration - added by install_shell_integration.ps1`n$sourceLine`n"
    Write-Output "Inserted shell integration line into $profilePath"
} else {
    Write-Output "Profile already contains shell integration line. No changes made."
}

Write-Output "Done. Restart your PowerShell/VS Code integrated terminal to test. Hover the terminal tab to see shell integration quality."