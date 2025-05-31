Get-ChildItem -Path . -Filter "*.test.ts" -Recurse | ForEach-Object {
    $newName = $_.FullName -replace '\.test\.ts$', '.test.mts'
    Rename-Item -Path $_.FullName -NewName $newName
} 