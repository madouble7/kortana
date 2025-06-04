@echo off
echo Collecting audit artifacts for Kor'tana...
cd %~dp0\..\
python scripts/collect_audit_artifacts.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to collect audit artifacts!
    exit /b %ERRORLEVEL%
) else (
    echo.
    echo Audit artifacts collected successfully!
    echo Results saved in audit_log.txt
    echo.
    echo Please also run the following commands in a fresh shell:
    echo.
    echo python -m venv .venv ^&^& .\.venv\Scripts\activate
    echo pip install -e .
    echo python -c "import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])"
    echo.
    exit /b 0
)
