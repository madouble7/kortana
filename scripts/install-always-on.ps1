#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Registers Kor'tana voice daemon + local daemon as Windows Task Scheduler
    tasks that start at user logon and auto-restart on failure.

.DESCRIPTION
    Creates two scheduled tasks:
      - kortana-voice-daemon:  always-on voice listener (mic → whisper → groq → piper)
      - kortana-local-daemon:  health monitor, git sync, break reminders

    Both run hidden (no visible window), start at logon, and restart on failure.
    The voice daemon's built-in supervisor handles crash recovery with backoff.

.NOTES
    Run from an elevated (Administrator) PowerShell prompt.
    To uninstall:  .\install-always-on.ps1 -Uninstall
#>
param(
    [switch]$Uninstall,
    [string]$PythonPath = "python",
    [string]$RepoRoot = "c:\kortana"
)

$ErrorActionPreference = "Stop"

$tasks = @(
    @{
        Name        = "kortana-voice-daemon"
        Description = "Kor'tana always-on voice listener (Silero VAD + faster-whisper + Groq + Piper)"
        Script      = "$RepoRoot\mcp-server\voice_daemon.py"
    },
    @{
        Name        = "kortana-local-daemon"
        Description = "Kor'tana local health monitor, git sync, and activity tracker"
        Script      = "$RepoRoot\mcp-server\local_daemon.py"
    }
)

if ($Uninstall) {
    foreach ($task in $tasks) {
        if (Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
            Write-Host "[OK] Removed: $($task.Name)" -ForegroundColor Yellow
        } else {
            Write-Host "[--] Not found: $($task.Name)" -ForegroundColor DarkGray
        }
    }
    Write-Host "`nkor'tana daemons uninstalled." -ForegroundColor Cyan
    exit 0
}

# Resolve python path
$resolvedPython = (Get-Command $PythonPath -ErrorAction SilentlyContinue).Source
if (-not $resolvedPython) {
    Write-Error "Python not found at '$PythonPath'. Pass -PythonPath <path> to specify."
    exit 1
}
Write-Host "Using Python: $resolvedPython" -ForegroundColor DarkGray

foreach ($task in $tasks) {
    Write-Host "`nRegistering: $($task.Name)..." -ForegroundColor Cyan

    # Remove existing if present
    if (Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
        Write-Host "  Replaced existing task." -ForegroundColor DarkGray
    }

    $action = New-ScheduledTaskAction `
        -Execute $resolvedPython `
        -Argument "`"$($task.Script)`"" `
        -WorkingDirectory $RepoRoot

    $trigger = New-ScheduledTaskTrigger -AtLogOn

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Days 0) `
        -MultipleInstances IgnoreNew

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $task.Name `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $task.Description | Out-Null

    Write-Host "  [OK] $($task.Name) registered." -ForegroundColor Green
}

Write-Host "`n--- kor'tana is immortal ---" -ForegroundColor Magenta
Write-Host "Both daemons will start automatically at logon and restart on failure."
Write-Host "To start now:  Start-ScheduledTask -TaskName 'kortana-voice-daemon'"
Write-Host "To stop:       Stop-ScheduledTask  -TaskName 'kortana-voice-daemon'"
Write-Host "To uninstall:  .\install-always-on.ps1 -Uninstall"
