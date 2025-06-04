@echo off
:: Activate venv311 environment for Project Kortana
echo Activating venv311 Python environment...
call C:\project-kortana\venv311\Scripts\activate.bat
echo Environment activated! Python path: %PYTHON%
echo.
echo You can now run Python scripts with the venv311 interpreter.
echo Try running: python verify_environment.py
