@echo off
echo ===== Kor'tana Environment Diagnostics =====
echo Running diagnostic tests and collecting results...

rem Create a diagnostics directory with timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set date=%%c-%%a-%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set time=%%a%%b)
set DIAG_DIR=diagnostics_%date%_%time%
mkdir %DIAG_DIR%

echo Creating diagnostics directory: %DIAG_DIR%

rem Step 1: Run basic execution test
echo.
echo ===== Running basic execution test =====
echo.
python test_exec.py > %DIAG_DIR%\exec_result.txt
type %DIAG_DIR%\exec_result.txt

rem Step 2: Run environment diagnostics
echo.
echo ===== Running environment diagnostics =====
echo.
python scripts\diagnose_environment.py > %DIAG_DIR%\diag_env_result.txt
type %DIAG_DIR%\diag_env_result.txt | more

rem Step 3: Run config loading test
echo.
echo ===== Running config loading test =====
echo.
python scripts\test_config_loading.py > %DIAG_DIR%\config_load_result.txt
echo Results saved to %DIAG_DIR%\config_load_result.txt

rem Step 4: Run integrated test
echo.
echo ===== Running integrated test =====
echo.
python test_config_integrated.py > %DIAG_DIR%\integrated_result.txt
type %DIAG_DIR%\integrated_result.txt | more

rem Step 5: Run audit collection
echo.
echo ===== Running audit collection =====
echo.
python scripts\collect_audit_artifacts_fixed.py
copy audit_log.txt %DIAG_DIR%\audit_log.txt

rem Create a summary file
echo.
echo ===== Creating summary =====
echo.
echo Kor'tana Diagnostic Summary > %DIAG_DIR%\summary.txt
echo Generated: %date% %time% >> %DIAG_DIR%\summary.txt
echo. >> %DIAG_DIR%\summary.txt
echo All diagnostic results are available in the %DIAG_DIR% directory. >> %DIAG_DIR%\summary.txt
echo. >> %DIAG_DIR%\summary.txt
echo Files included: >> %DIAG_DIR%\summary.txt
echo - exec_result.txt: Basic Python execution environment information >> %DIAG_DIR%\summary.txt
echo - diag_env_result.txt: Detailed environment diagnostic information >> %DIAG_DIR%\summary.txt
echo - config_load_result.txt: Configuration loading test results >> %DIAG_DIR%\summary.txt
echo - integrated_result.txt: Integrated environment and config test >> %DIAG_DIR%\summary.txt
echo - audit_log.txt: Full audit results >> %DIAG_DIR%\summary.txt
echo. >> %DIAG_DIR%\summary.txt
echo IMPORTANT: Do not proceed with config code or environment refactors >> %DIAG_DIR%\summary.txt
echo until sanctuary (matt) has reviewed and confirmed a stable, >> %DIAG_DIR%\summary.txt
echo reproducible environment based on these diagnostic outputs. >> %DIAG_DIR%\summary.txt

echo.
echo ===== Diagnostics Complete =====
echo.
echo All diagnostic results have been saved to the %DIAG_DIR% directory.
echo Please review the files and share them with sanctuary (matt) for analysis.
echo No changes to configuration code should be made until after review.
echo.
