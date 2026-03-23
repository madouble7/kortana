# PowerShell script to create PostgreSQL user and database
# Using PostgreSQL command-line tools with Windows authentication

$psqlPath = "C:\Program Files\PostgreSQL\15\bin\psql.exe"
$pgHome = "C:\Program Files\PostgreSQL\15"

# Set environment for psql
$env:PGPASSWORD = "postgres"  # Change this to your actual postgres password

# Check if psql exists
if (-not (Test-Path $psqlPath)) {
    Write-Host "PostgreSQL psql not found at: $psqlPath"
    Write-Host "Searching for psql..."
    $psqlPath = Get-ChildItem -Path "C:\Program Files" -Filter "psql.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

    if (-not $psqlPath) {
        Write-Host "❌ PostgreSQL psql.exe not found on system"
        exit 1
    }
}

Write-Host "Using psql: $psqlPath"

# SQL commands to execute
$sqlCommands = @"
CREATE DATABASE IF NOT EXISTS kortana;
CREATE USER matt WITH PASSWORD 'iamwhoiam';
ALTER USER matt WITH SUPERUSER CREATEDB LOGIN;
GRANT ALL PRIVILEGES ON DATABASE kortana TO matt;
GRANT ALL ON SCHEMA public TO matt;
"@

# Write SQL to temp file
$tempSqlFile = "$env:TEMP\setup_db_temp.sql"
$sqlCommands | Out-File -FilePath $tempSqlFile -Encoding UTF8

# Execute psql with the SQL file
Write-Host "Creating database and user..."
& $psqlPath -U postgres -h localhost -f $tempSqlFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database setup complete!"
    Remove-Item $tempSqlFile -Force
}
else {
    Write-Host "❌ Database setup failed with exit code: $LASTEXITCODE"
    Remove-Item $tempSqlFile -Force
    exit 1
}
