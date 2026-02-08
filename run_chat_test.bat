@echo off
cd /d C:\kortana
set PYTHONPATH=C:\kortana\src
"C:\kortana\.kortana_config_test_env\Scripts\python.exe" test_chat_interactive.py
pause
