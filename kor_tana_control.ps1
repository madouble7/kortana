#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Kor'tana Control Script - Interact with the autonomous development system
.DESCRIPTION
    Easy PowerShell interface for controlling and monitoring Kor'tana
#>

param(
    [ValidateSet('status', 'start', 'stop', 'check', 'tasks', 'dashboard', 'metrics', 'health', 'approve', 'retry')]
    [string]$Action = "status",
    [string]$TaskId = "",
    [bool]$Approved = $true,
    [string]$Notes = ""
)

$BaseUrl = "http://localhost:8000/api/always-on"
$ErrorActionPreference = "Continue"

function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Write-Section {
    param([string]$Text)
    Write-Host "`n▶ $Text" -ForegroundColor Green
    Write-Host ("─" * 60) -ForegroundColor Gray
}

function Invoke-KorApi {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Body = $null
    )

    try {
        $Url = "$BaseUrl/$Endpoint"
        $Params = @{
            Uri         = $Url
            Method      = $Method
            ContentType = "application/json"
            TimeoutSec  = 10
        }

        if ($Body) {
            $Params.Body = ($Body | ConvertTo-Json)
        }

        $Response = Invoke-RestMethod @Params
        return $Response
    }
    catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
        return $null
    }
}

function Format-Output {
    param([object]$Data)
    $Data | ConvertTo-Json -Depth 5 | Write-Host
}

# Main execution
Write-Header "🤖 KOR'TANA CONTROL SYSTEM"

switch ($Action) {
    "status" {
        Write-Section "Always-On Monitor Status"
        $Status = Invoke-KorApi "status"
        if ($Status) {
            Format-Output $Status
        }
    }

    "start" {
        Write-Section "Starting Always-On Monitoring..."
        $Result = Invoke-KorApi "start" -Method POST
        if ($Result) {
            Write-Host "✅ " -NoNewline -ForegroundColor Green
            Write-Host $Result.message
            Format-Output $Result
        }
    }

    "stop" {
        Write-Section "Stopping Always-On Monitoring..."
        $Result = Invoke-KorApi "stop" -Method POST
        if ($Result) {
            Write-Host "⏹️  " -NoNewline -ForegroundColor Yellow
            Write-Host $Result.message
            Format-Output $Result
        }
    }

    "check" {
        Write-Section "Forcing Immediate Monitoring Cycle..."
        $Result = Invoke-KorApi "force-check" -Method POST
        if ($Result) {
            Write-Host "⚡ " -NoNewline -ForegroundColor Yellow
            Write-Host "Check initiated"
            Format-Output $Result
        }
    }

    "tasks" {
        Write-Section "Recent Tasks"
        $Tasks = Invoke-KorApi "tasks?limit=10"
        if ($Tasks) {
            Format-Output $Tasks
        }
    }

    "dashboard" {
        Write-Section "Full Dashboard"
        $Dashboard = Invoke-KorApi "dashboard"
        if ($Dashboard) {
            Format-Output $Dashboard
        }
    }

    "metrics" {
        Write-Section "System Metrics"
        $Metrics = Invoke-KorApi "metrics"
        if ($Metrics) {
            Format-Output $Metrics
        }
    }

    "health" {
        Write-Section "Health Check"
        $Health = Invoke-KorApi "health"
        if ($Health) {
            Write-Host "Status: " -NoNewline
            Write-Host $Health.status -ForegroundColor Green
            Format-Output $Health
        }
    }

    "approve" {
        if (-not $TaskId) {
            Write-Host "❌ Task ID required for approve action" -ForegroundColor Red
            exit 1
        }

        Write-Section "Approving Task: $TaskId"
        $Result = Invoke-KorApi "tasks/$TaskId/approve" -Method POST -Body @{
            approved = $Approved
            notes    = $Notes
        }

        if ($Result) {
            Write-Host "✅ " -NoNewline -ForegroundColor Green
            Write-Host $Result.message
            Format-Output $Result
        }
    }

    "retry" {
        if (-not $TaskId) {
            Write-Host "❌ Task ID required for retry action" -ForegroundColor Red
            exit 1
        }

        Write-Section "Retrying Task: $TaskId"
        $Result = Invoke-KorApi "tasks/$TaskId/retry" -Method POST

        if ($Result) {
            Write-Host "🔄 " -NoNewline -ForegroundColor Yellow
            Write-Host $Result.message
            Format-Output $Result
        }
    }

    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Operation complete`n" -ForegroundColor Green
