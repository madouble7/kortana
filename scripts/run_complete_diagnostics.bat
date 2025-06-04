@echo off
echo ===== Kor'tana Complete Environment Diagnostics =====
echo Running all diagnostic tests and collecting results...

rem Create results directory
set RESULTS_DIR=diagnostic_results
if not exist %RESULTS_DIR% mkdir %RESULTS_DIR%

rem Step 1: Run test_exec.py
echo.
echo [1/6] Running basic execution test...
python test_exec.py > %RESULTS_DIR%\exec_result.txt
echo Results saved to %RESULTS_DIR%\exec_result.txt
type %RESULTS_DIR%\exec_result.txt

rem Step 2: Run diagnose_environment.py
echo.
echo [2/6] Running environment diagnostics...
python scripts\diagnose_environment.py > %RESULTS_DIR%\diag_env_result.txt
echo Results saved to %RESULTS_DIR%\diag_env_result.txt

rem Step 3: Run test_config_loading.py
echo.
echo [3/6] Testing configuration loading...
python scripts\test_config_loading.py > %RESULTS_DIR%\config_load_result.txt
echo Results saved to %RESULTS_DIR%\config_load_result.txt

rem Step 4: Run test_config_integrated.py
echo.
echo [4/6] Running integrated test...
python test_config_integrated.py > %RESULTS_DIR%\integrated_result.txt
echo Results saved to %RESULTS_DIR%\integrated_result.txt

rem Step 5: Run full audit collection
echo.
echo [5/6] Running audit collection...
python scripts\collect_audit_artifacts.py
copy audit_log.txt %RESULTS_DIR%\audit_log.txt

rem Step 6: Create summary report
echo.
echo [6/6] Creating summary report...
echo Kor'tana Environment Diagnostic Summary > %RESULTS_DIR%\summary.txt
echo ======================================= >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Generated: %DATE% %TIME% >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Environment Information: >> %RESULTS_DIR%\summary.txt
echo --------------------- >> %RESULTS_DIR%\summary.txt
findstr "Python Version" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
findstr "Python Executable" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
findstr "Current Working Directory" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
findstr "Active Virtual Environment" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo First sys.path entries: >> %RESULTS_DIR%\summary.txt
findstr /n "\[0\]" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
findstr /n "\[1\]" %RESULTS_DIR%\diag_env_result.txt >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Configuration Status: >> %RESULTS_DIR%\summary.txt
echo ------------------- >> %RESULTS_DIR%\summary.txt
findstr "load_config function exists" %RESULTS_DIR%\config_load_result.txt >> %RESULTS_DIR%\summary.txt
findstr "load_config() executed successfully" %RESULTS_DIR%\config_load_result.txt >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo *** IMPORTANT: *** >> %RESULTS_DIR%\summary.txt
echo Do NOT proceed with any config code or environment changes >> %RESULTS_DIR%\summary.txt
echo until sanctuary (matt) has reviewed these diagnostic results. >> %RESULTS_DIR%\summary.txt

echo.
echo ===== Diagnostics Complete =====
echo.
echo All diagnostic results have been saved to the %RESULTS_DIR% directory.
echo Please review the following files:
echo   - exec_result.txt: Basic Python execution environment
echo   - diag_env_result.txt: Detailed environment diagnostics
echo   - config_load_result.txt: Configuration loading test results
echo   - integrated_result.txt: Integrated environment and config test
echo   - audit_log.txt: Complete audit artifacts
echo   - summary.txt: Summary of key diagnostic information
echo.
echo IMPORTANT: Do NOT proceed with any config code or environment changes
echo until sanctuary (matt) has reviewed these diagnostic results.
echo.
