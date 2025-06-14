@echo off
python test_architecture_focused.py > focused_result.txt 2>&1
echo Focused architectural test completed, checking result...
type focused_result.txt
