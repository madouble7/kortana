@echo off
setlocal enabledelayedexpansion

cd /d c:\kortana
set PYTHONPATH=c:\kortana\src
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

python -m pytest tests/ -v --tb=short

pause
