@echo off
echo Starting diagnostic test...
C:\project-kortana\venv311\Scripts\python.exe C:\project-kortana\arch_test_script.py > arch_output_from_batch.txt 2>&1
echo Test completed. Output has been redirected to arch_output_from_batch.txt
type arch_output_from_batch.txt
