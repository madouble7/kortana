# Script: root_directory.ps1
# Purpose: Lists only the root-level files and folders in the current directory and saves to root_directory.txt
# Usage: Run this script from your project root directory

$outputFile = "root_directory.txt"
Write-Host "`n--- Generating root directory file/folder list to '$outputFile' ---"

# Get root directory name
$rootDirName = (Get-Item .).Name
$fileList = @("# Root Directory Listing for /$rootDirName/")
$fileList += "# Last Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$fileList += "" # Blank line

# List all files and folders at the root (no recursion)
Get-ChildItem -Path . | Sort-Object Name | ForEach-Object {
    if ($_.PSIsContainer) {
        $fileList += "/$($_.Name)/"  # Folder
    } else {
        $fileList += $($_.Name)       # File
    }
}

# Save to file
Set-Content -Path $outputFile -Value ($fileList | Out-String)

Write-Host "Root directory file/folder list saved to '$outputFile'"
