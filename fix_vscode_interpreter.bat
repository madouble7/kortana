@echo off 
echo Running VS Code Python Extension Cache Fix... 
echo. 
echo 1. Make sure VS Code is completely closed before continuing 
echo. 
pause 
echo. 
echo Clearing VS Code Python extension cache... 
if exist "%C:\Users\madou%\.vscode\extensions\ms-python.python-*" ( 
    echo Found Python extension directory 
    for /d %%%%i in ("%C:\Users\madou%\.vscode\extensions\ms-python.python-*") do ( 
        echo Clearing cache in: %%%%i 
        if exist "%%%%i\pythonFiles\lib\python\debugpy\_vendored\pydevd\pydevd_attach_to_process" rd /s /q "%%%%i\pythonFiles\lib\python\debugpy\_vendored\pydevd\pydevd_attach_to_process" 
        echo Cache directories removed 
    ) 
) else ( 
    echo Python extension directory not found 
) 
echo. 
echo Creating verification file to test the Python interpreter... 
echo import sysprint(f"Interpreter path: {sys.executable}")print(f"Python version: {sys.version}") 
echo. 
echo Running Python verification with venv311... 
C:\project-kortana\venv311\Scripts\python.exe C:\project-kortana\verify_python.py 
echo. 
echo Done. Please restart VS Code and try selecting the Python interpreter again. 
pause 
