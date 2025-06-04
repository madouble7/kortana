@echo off
echo Running config verification tests...
cd %~dp0\..\
python -m scripts.verify_config_pipeline
if %ERRORLEVEL% NEQ 0 (
    echo Config tests failed!
    exit /b %ERRORLEVEL%
) else (
    echo Config tests passed!
    exit /b 0
)
