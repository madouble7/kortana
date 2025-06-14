@echo off
ECHO Opening Project Kortana in VS Code...
:: Use the workspace file to ensure consistent startup
start "" "code" "C:\project-kortana\project-kortana.code-workspace"
ECHO If VS Code opens in a limited view, close it and run this script again.
