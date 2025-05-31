# Script: project_files.ps1
# Purpose: Generates a recursive tree structure of key project files and folders.
# Context: Used by Project Kor'tana / Sacred Circuit for comprehensive project context.
# Ensure you are in your project root directory first in PowerShell before running, e.g.,
# cd "C:\kortana"

$outputFile = "project_files.txt"
$rootDirName = (Get-Item .).Name
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

Write-Host "`n--- Generating comprehensive file list to '$outputFile' at $timestamp ---"

# Initialize content array
$fileList = @()
$fileList += "# Sacred Circuit Project Overview"
$fileList += "# Root Directory: /$rootDirName/"
$fileList += "# Last Updated: $timestamp"
$fileList += ""

# Exclude noise and generated directories/files
$excludeList = @(".git", ".venv", "venv311", "__pycache__", "node_modules", ".DS_Store", ".gradio", "test-results", "test_outputs", "notebooks")

# --- Important Root Level Files (Soulprint) ---
$fileList += "--- Important Root Level Files (Soulprint) ---"
$soulprintFiles = @("README.md", "KORTANA_PROJECT_STATE_LIVE.md", "Kor'tana.Decisions.md", "kortana_copilot_instructions.md")

foreach ($file in $soulprintFiles) {
    if (Test-Path $file) {
        $fileList += "✨ $($file) ✨"
    }
    else {
        $fileList += "❓ $($file) (Not Found) ❓"
    }
}
$fileList += ""

# --- Function to recursively list files and folders for a given path with exclusions ---
function Get-DetailedDirectoryTree($targetPath, $parentIndent = "", $isLastParent = $false) {
    $localFileList = @()
    $items = Get-ChildItem -Path $targetPath -Force | Where-Object {
        -not ($excludeList -contains $_.Name)
    } | Sort-Object @{Expression = "PSIsContainer"; Descending = $true }, Name

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLastItem = ($i -eq $items.Count - 1)

        $prefix = if ($isLastItem) { "\-- " } else { "|-- " }

        if ($item.PSIsContainer) {
            $localFileList += "$($parentIndent)$($prefix)$($item.Name)/"
            $newIndent = if ($isLastItem) { "$($parentIndent)    " } else { "$($parentIndent)|   " }
            $localFileList += Get-DetailedDirectoryTree -targetPath $item.FullName -parentIndent $newIndent -isLastParent $isLastItem
        }
        else {
            $localFileList += "$($parentIndent)$($prefix)$($item.Name)"
        }
    }
    return $localFileList
}

# --- List Contents of Key Subdirectories (Recursive) ---
$subDirsToScan = @(
    "config",
    "src",
    "kortana.core", # Assuming this exists for soulprint docs
    "kortana.network" # Assuming this exists for network-related code
)

foreach ($subDir in $subDirsToScan) {
    if (Test-Path $subDir) {
        $fileList += "--- Subdirectory: $($subDir)/ ---"
        $fileList += Get-DetailedDirectoryTree -targetPath $subDir
        $fileList += "" # Blank line after each main subdirectory
    }
    else {
        $fileList += "--- Subdirectory: $($subDir)/ --- (Not Found)"
        $fileList += ""
    }
}

# --- Save to file ---
Set-Content -Path $outputFile -Value ($fileList | Out-String)

Write-Host "Comprehensive file list saved to '$outputFile'"
Write-Host "Review '$outputFile' to see the generated project structure."
