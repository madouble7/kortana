@echo off
echo 🔧 VENV311 PATH DIAGNOSTIC & FIX
echo.

echo 📍 Checking venv311 directory structure:
if exist "c:\kortana\venv311" (
    echo ✅ venv311 directory exists
) else (
    echo ❌ venv311 directory NOT found
    echo Creating venv311...
    python -m venv c:\kortana\venv311
)

echo.
echo 📍 Checking Python executable:
if exist "c:\kortana\venv311\Scripts\python.exe" (
    echo ✅ Python executable found at c:\kortana\venv311\Scripts\python.exe
) else (
    echo ❌ Python executable NOT found
    if exist "c:\kortana\venv311\Scripts\python3.exe" (
        echo ✅ Found python3.exe instead
        copy "c:\kortana\venv311\Scripts\python3.exe" "c:\kortana\venv311\Scripts\python.exe"
    )
)

echo.
echo 📍 Current Python installations:
where python

echo.
echo 📍 Activating venv311 and testing:
call c:\kortana\venv311\Scripts\activate.bat
echo Virtual environment: %VIRTUAL_ENV%
python --version
python -c "import sys; print('Python path:', sys.executable)"

echo.
echo 💡 To fix VS Code:
echo 1. Open VS Code
echo 2. Ctrl+Shift+P → "Python: Select Interpreter"
echo 3. Choose: c:\kortana\venv311\Scripts\python.exe
echo 4. Or manually edit .vscode\settings.json

pause
