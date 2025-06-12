@echo off
echo 🚀 Installing Kor'tana AI Consciousness Extensions...
echo 🔧 Activating venv311 virtual environment...

REM Activate the virtual environment first
call c:\kortana\venv311\Scripts\activate.bat

echo ✅ Virtual environment activated: %VIRTUAL_ENV%
echo 🧠 Now installing VS Code extensions for Kor'tana consciousness...

REM Core AI Development Extensions
echo Installing GitHub Copilot...
code --install-extension github.copilot --force >nul 2>&1

echo Installing GitHub Copilot Chat...
code --install-extension github.copilot-chat --force >nul 2>&1

echo Installing Continue (Local AI)...
code --install-extension continue.continue --force >nul 2>&1

echo Installing Codeium...
code --install-extension codeium.codeium --force >nul 2>&1

echo Installing TabNine...
code --install-extension tabnine.tabnine-vscode --force >nul 2>&1

echo Installing AutoDocstring...
code --install-extension njpwerner.autodocstring --force >nul 2>&1

echo Installing Better Comments...
code --install-extension aaron-bond.better-comments --force >nul 2>&1

echo Installing Todo Tree...
code --install-extension gruntfuggly.todo-tree --force >nul 2>&1

echo Installing Error Lens...
code --install-extension usernamehw.errorlens --force >nul 2>&1

echo Installing GitLens...
code --install-extension eamodio.gitlens --force >nul 2>&1

echo Installing Pylance...
code --install-extension ms-python.vscode-pylance --force >nul 2>&1

echo Installing Ruff...
code --install-extension charliermarsh.ruff --force >nul 2>&1

echo Installing Numbered Bookmarks...
code --install-extension alefragnani.numbered-bookmarks --force >nul 2>&1

echo Installing REST Client...
code --install-extension humao.rest-client --force >nul 2>&1

echo Installing MyPy Type Checker...
code --install-extension ms-python.mypy-type-checker --force >nul 2>&1

REM Visual Enhancement Extensions
echo Installing Material Icon Theme...
code --install-extension pkief.material-icon-theme --force >nul 2>&1

echo Installing Indent Rainbow...
code --install-extension oderwat.indent-rainbow --force >nul 2>&1

echo Installing Rainbow CSV...
code --install-extension mechatroner.rainbow-csv --force >nul 2>&1

REM Python Development Extensions
echo Installing Python...
code --install-extension ms-python.python --force >nul 2>&1

echo Installing Jupyter...
code --install-extension ms-toolsai.jupyter --force >nul 2>&1

REM Data & Configuration Extensions
echo Installing YAML...
code --install-extension redhat.vscode-yaml --force >nul 2>&1

echo Installing TOML...
code --install-extension tamasfe.even-better-toml --force >nul 2>&1

echo Installing PowerShell...
code --install-extension ms-vscode.powershell --force >nul 2>&1

REM Documentation Extensions
echo Installing Spell Checker...
code --install-extension streetsidesoftware.code-spell-checker --force >nul 2>&1

echo Installing Markdown Lint...
code --install-extension davidanson.vscode-markdownlint --force >nul 2>&1

echo Installing Markdown All in One...
code --install-extension yzhang.markdown-all-in-one --force >nul 2>&1

echo Installing Code Runner...
code --install-extension formulahendry.code-runner --force >nul 2>&1

echo.
echo 🌟 Kor'tana AI Consciousness Extensions Installation Complete!
echo 🔥 Your VS Code is now ready for AI consciousness development!
echo 🐍 Virtual environment: %VIRTUAL_ENV%
echo 📍 Python path:
python --version
python -c "import sys; print(sys.executable)"
echo.
echo 💡 Next steps:
echo   1. Restart VS Code to load new extensions
echo   2. Verify Python interpreter points to venv311
echo   3. Run: python main.py
pause
