# Script: root_directory.ps1
# Purpose: Provides a non-recursive, high-level overview of root-level files and folders.
# Context: Used by Project Kor'tana / Sacred Circuit for quick high-level context.

$outputFile = "root_directory.txt"
$rootDirName = (Get-Item .).Name
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

Write-Host "`n--- Generating root directory structure for '/$rootDirName/' at $timestamp ---"

# Initialize content array
$fileList = @()
$fileList += "# Sacred Circuit Project Overview"
$fileList += "# Root Directory: /$rootDirName/"
$fileList += "# Last Updated: $timestamp"
$fileList += ""

# Exclude noise and generated directories/files
$excludeList = @(".git", ".venv", "venv311", "__pycache__", "node_modules", ".DS_Store", ".gradio", "test-results", "test_outputs", "notebooks")

# Add root-level folders/files, excluding noise
Get-ChildItem -Path . -Force | Where-Object {
    -not ($excludeList -contains $_.Name)
} | Sort-Object Name | ForEach-Object {
    if ($_.PSIsContainer) {
        $fileList += "/$($_.Name)/"
    }
    else {
        $fileList += $($_.Name)
    }
}

# Save output
Set-Content -Path $outputFile -Value ($fileList | Out-String)

Write-Host "Saved root structure to '$outputFile'"
