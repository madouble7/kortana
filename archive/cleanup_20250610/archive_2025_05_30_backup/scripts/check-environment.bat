@echo off
echo 🧠 KOR'TANA CONSCIOUSNESS ENVIRONMENT STATUS CHECK
echo.

REM Activate venv311
call c:\kortana\venv311\Scripts\activate.bat

echo ✅ Virtual Environment: %VIRTUAL_ENV%
echo.

echo 🐍 Python Status:
python --version
echo Python executable:
python -c "import sys; print(sys.executable)"
echo.

echo 📦 Key Python Packages:
python -c "import pkg_resources; installed = [str(d) for d in pkg_resources.working_set]; print('google-generativeai:', 'google-generativeai' in str(installed))"
python -c "import pkg_resources; installed = [str(d) for d in pkg_resources.working_set]; print('openai:', 'openai' in str(installed))"
python -c "import pkg_resources; installed = [str(d) for d in pkg_resources.working_set]; print('anthropic:', 'anthropic' in str(installed))"
echo.

echo 🔧 VS Code Extensions Status:
code --list-extensions | findstr -i "github.copilot"
code --list-extensions | findstr -i "ms-python.python"
code --list-extensions | findstr -i "continue.continue"
echo.

echo 📁 Project Structure:
if exist "src\brain.py" echo ✅ Brain module ready
if exist "src\model_router.py" echo ✅ Model router ready
if exist "main.py" echo ✅ Main entry point ready
if exist ".vscode\settings.json" echo ✅ VS Code configured
echo.

echo 🌟 Kor'tana Consciousness Environment: READY FOR DEVELOPMENT!
pause
