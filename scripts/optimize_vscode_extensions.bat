@echo off
echo =====================================================
echo VS Code Extension Optimization for GitHub Copilot
echo =====================================================
echo.
echo This script will help optimize your VS Code extensions
echo for better GitHub Copilot performance.
echo.

REM First, let's disable the heavy extensions
echo Disabling heavy Jupyter extensions (can re-enable when needed)...
code --disable-extension ms-toolsai.jupyter
code --disable-extension ms-toolsai.jupyter-keymap
code --disable-extension ms-toolsai.jupyter-renderers
code --disable-extension ms-toolsai.vscode-jupyter-cell-tags
code --disable-extension ms-toolsai.vscode-jupyter-slideshow

echo.
echo Disabling redundant test extensions...
code --disable-extension hbenl.vscode-test-explorer
code --disable-extension littlefoxteam.vscode-python-test-adapter
code --disable-extension ms-vscode.test-adapter-converter

echo.
echo Disabling potentially conflicting AI extensions...
code --disable-extension google.geminicodeassist

echo.
echo Disabling container extensions (unless you use Docker)...
code --disable-extension anysphere.remote-containers
code --disable-extension ms-azuretools.vscode-docker
code --disable-extension ms-vscode-remote.remote-containers

echo.
echo Disabling specialized tools that may slow down workspace...
code --disable-extension mechatroner.rainbow-csv
code --disable-extension ms-vscode.powershell
code --disable-extension ms-vscode.vscode-speech
code --disable-extension wayou.vscode-todo-highlight

echo.
echo =====================================================
echo Optimization Complete!
echo =====================================================
echo.
echo Your essential extensions are still active:
echo - GitHub Copilot and Copilot Chat
echo - Python language support (Pylance, debugger)
echo - YAML support for config files
echo - Markdown support for documentation
echo.
echo Disabled extensions can be re-enabled when needed via:
echo   Ctrl+Shift+X ^> Search for extension ^> Enable
echo.
echo Restart VS Code for changes to take effect.
echo.
pause
