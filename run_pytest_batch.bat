@echo off
echo Running pytest and capturing output...
cd /d C:\project-kortana
set PYTHONPATH=C:\project-kortana;C:\project-kortana\src
C:\project-kortana\venv311\Scripts\python.exe -m pytest tests/unit/ -v > C:\project-kortana\pytest_batch_output.txt 2>&1
echo Test run completed.
echo Output saved to: C:\project-kortana\pytest_batch_output.txt
echo ----------------------
echo File information:
dir C:\project-kortana\pytest_batch_output.txt 2>nul || echo File not created!
