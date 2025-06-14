@echo off
echo ===== Kor'tana Environment Diagnostics Package =====
echo Preparing complete diagnostic package for sanctuary...
echo.

rem Create results directory with timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set date=%%c%%a%%b)
for /f "tokens=1-2 delims=:." %%a in ('time /t') do (set time=%%a%%b)
set RESULTS_DIR=diagnostic_results
if not exist %RESULTS_DIR% mkdir %RESULTS_DIR%

echo Creating diagnostics directory: %RESULTS_DIR%

rem Step 0: Create README for diagnostics
echo.
echo [0/8] Creating README for diagnostics...
python scripts\create_diagnostics_readme.py

rem Step 1: Run test_exec.py
echo.
echo [1/8] Running basic execution test...
python test_exec.py > %RESULTS_DIR%\exec_result.txt
echo Results saved to %RESULTS_DIR%\exec_result.txt
type %RESULTS_DIR%\exec_result.txt

rem Step 2: Generate environment report
echo.
echo [2/8] Generating environment report...
python scripts\generate_environment_report.py

rem Step 3: Run environment diagnostics
echo.
echo [3/8] Running environment diagnostics...
python scripts\diagnose_environment.py > %RESULTS_DIR%\diag_env_result.txt
echo Results saved to %RESULTS_DIR%\diag_env_result.txt

rem Step 4: Test config loading
echo.
echo [4/8] Testing configuration loading...
python scripts\test_config_loading.py > %RESULTS_DIR%\config_load_result.txt
echo Results saved to %RESULTS_DIR%\config_load_result.txt

rem Step 5: Run integrated test
echo.
echo [5/8] Running integrated test...
python test_config_integrated.py > %RESULTS_DIR%\integrated_result.txt
echo Results saved to %RESULTS_DIR%\integrated_result.txt

rem Step 6: Run full audit collection
echo.
echo [6/8] Running audit collection...
python scripts\collect_audit_artifacts.py
copy audit_log.txt %RESULTS_DIR%\audit_log.txt

rem Step 7: Create summary
echo.
echo [7/8] Creating diagnostic summary...
echo Kor'tana Environment Diagnostic Summary > %RESULTS_DIR%\summary.txt
echo ======================================= >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Generated: %DATE% %TIME% >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Environment Information: >> %RESULTS_DIR%\summary.txt
echo --------------------- >> %RESULTS_DIR%\summary.txt
findstr "Python Version" %RESULTS_DIR%\exec_result.txt >> %RESULTS_DIR%\summary.txt
findstr "Python Executable" %RESULTS_DIR%\exec_result.txt >> %RESULTS_DIR%\summary.txt
findstr "Current Working Directory" %RESULTS_DIR%\exec_result.txt >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Python Path: >> %RESULTS_DIR%\summary.txt
findstr "\[0\]" %RESULTS_DIR%\exec_result.txt >> %RESULTS_DIR%\summary.txt
findstr "\[1\]" %RESULTS_DIR%\exec_result.txt >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Configuration Status: >> %RESULTS_DIR%\summary.txt
echo ------------------- >> %RESULTS_DIR%\summary.txt
echo Look for these indicators in config_load_result.txt: >> %RESULTS_DIR%\summary.txt
echo - "load_config function exists" >> %RESULTS_DIR%\summary.txt
echo - "load_config() executed successfully" >> %RESULTS_DIR%\summary.txt
echo - "Found YAML file: default.yaml" >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo Integrated Test Result: >> %RESULTS_DIR%\summary.txt
echo ------------------- >> %RESULTS_DIR%\summary.txt
echo Look for these indicators in integrated_result.txt: >> %RESULTS_DIR%\summary.txt
echo - "Config module imported successfully" >> %RESULTS_DIR%\summary.txt
echo - "Configuration loaded successfully" >> %RESULTS_DIR%\summary.txt
echo. >> %RESULTS_DIR%\summary.txt
echo *** IMPORTANT NOTES *** >> %RESULTS_DIR%\summary.txt
echo 1. Review all files in the diagnostic_results directory >> %RESULTS_DIR%\summary.txt
echo 2. Check if Python is running from the expected virtual environment >> %RESULTS_DIR%\summary.txt
echo 3. Verify that the config module is found and loaded correctly >> %RESULTS_DIR%\summary.txt
echo 4. Check if YAML files are found in the expected location >> %RESULTS_DIR%\summary.txt
echo 5. DO NOT proceed with any code or environment changes >> %RESULTS_DIR%\summary.txt
echo   until these results are reviewed by sanctuary (matt) >> %RESULTS_DIR%\summary.txt

rem Step 8: Package the results
echo.
echo [8/8] Packaging diagnostic results...
if exist %RESULTS_DIR%.zip del %RESULTS_DIR%.zip
powershell -command "Compress-Archive -Path '%RESULTS_DIR%' -DestinationPath '%RESULTS_DIR%.zip'"
echo Results packaged as %RESULTS_DIR%.zip

echo.
echo ===== Diagnostics Package Complete =====
echo.
echo All diagnostic results have been saved to the %RESULTS_DIR% directory
echo and packaged as %RESULTS_DIR%.zip
echo.
echo Please share these results with sanctuary (matt) for review.
echo.
echo IMPORTANT: Do NOT proceed with any config code or environment changes
echo until sanctuary (matt) has reviewed these diagnostic results.
echo.
