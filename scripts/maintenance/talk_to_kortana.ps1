#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick launcher for Kor'tana chat interfaces
.DESCRIPTION
    Choose and launch your preferred chat interface with Kor'tana
#>

$choices = @(
    "Simple Chat (No setup needed - Start here!)",
    "Full Chat (Requires server)",
    "Voice Chat (Requires server + microphone)",
    "Exit"
)

do {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  TALK TO KOR'TANA - Choose Your Interface" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $choices.Count; $i++) {
        Write-Host "  $($i + 1). $($choices[$i])" -ForegroundColor Yellow
    }

    Write-Host ""
    $choice = Read-Host "Enter your choice (1-4)"

    switch ($choice) {
        "1" {
            Write-Host "`n🚀 Starting Simple Chat..." -ForegroundColor Green
            Write-Host "✨ No setup required!" -ForegroundColor Cyan
            Write-Host "💡 Tip: Type 'help' for all commands`n" -ForegroundColor Gray

            & python kor_tana_simple_chat.py
            break
        }
        "2" {
            Write-Host "`n⚠️  Full Chat requires the server running!" -ForegroundColor Yellow
            Write-Host "`nStarting server check..." -ForegroundColor Cyan

            $response = try {
                Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2
                $true
            }
            catch {
                $false
            }

            if ($response) {
                Write-Host "✅ Server is running!`n" -ForegroundColor Green
                Write-Host "🚀 Starting Full Chat..." -ForegroundColor Green
                Write-Host "💡 Tip: Type 'help' for all commands`n" -ForegroundColor Gray

                & python kor_tana_chat.py
            }
            else {
                Write-Host "❌ Server not running on port 8000" -ForegroundColor Red
                Write-Host "Start it with:
  cd backend
  python -m uvicorn src.kortana.main:app --port 8000`n" -ForegroundColor Yellow

                $start = Read-Host "Start server now? (y/n)"
                if ($start -eq 'y') {
                    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn src.kortana.main:app --port 8000"
                    Start-Sleep -Seconds 5
                    & python kor_tana_chat.py
                }
            }
            break
        }
        "3" {
            Write-Host "`n⚠️  Voice Chat requires: Server + Microphone + Speakers!" -ForegroundColor Yellow
            Write-Host "`nStarting server check..." -ForegroundColor Cyan

            $response = try {
                Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2
                $true
            }
            catch {
                $false
            }

            if ($response) {
                Write-Host "✅ Server is running!`n" -ForegroundColor Green
                Write-Host "🎤 Starting Voice Chat..." -ForegroundColor Green
                Write-Host "💡 Make sure your microphone is connected!`n" -ForegroundColor Gray

                & python kor_tana_voice_chat.py
            }
            else {
                Write-Host "❌ Server not running on port 8000" -ForegroundColor Red
                Write-Host "Start it with:
  cd backend
  python -m uvicorn src.kortana.main:app --port 8000`n" -ForegroundColor Yellow

                $start = Read-Host "Start server now? (y/n)"
                if ($start -eq 'y') {
                    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn src.kortana.main:app --port 8000"
                    Start-Sleep -Seconds 5
                    & python kor_tana_voice_chat.py
                }
            }
            break
        }
        "4" {
            Write-Host "`nGoodbye! 👋`n" -ForegroundColor Cyan
            exit
        }
        default {
            Write-Host "`n❌ Invalid choice. Please try again.`n" -ForegroundColor Red
        }
    }

} while ($true)

