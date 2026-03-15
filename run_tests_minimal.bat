@echo off
cd /d c:\kortana
SET PYTHONPATH=c:\kortana\src
SET PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests\ -v --tb=short -x
