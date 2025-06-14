@echo off
echo Running Kor'tana audit collection...
python scripts/audit.py
if %ERRORLEVEL% NEQ 0 (
    echo Error running audit collection!
    exit /b %ERRORLEVEL%
)

echo.
echo Audit complete! Results saved in audit_log.txt
echo.
echo REMINDER:
echo Please run the installation test manually in a fresh shell:
echo python -m venv .venv ^&^& .\.venv\Scripts\activate
echo pip install -e .
echo python -c "import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])"
