@echo off
echo =====================================================
echo VS Code Extension Management - Interactive Mode
echo =====================================================
echo.

:menu
echo Choose an optimization level:
echo.
echo 1. MINIMAL - Keep only essential Python + Copilot extensions
echo 2. MODERATE - Disable heavy extensions but keep useful ones
echo 3. SELECTIVE - Choose which extensions to disable manually
echo 4. REVERT - Re-enable all previously disabled extensions
echo 5. STATUS - Show current extension status
echo 6. EXIT
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto minimal
if "%choice%"=="2" goto moderate
if "%choice%"=="3" goto selective
if "%choice%"=="4" goto revert
if "%choice%"=="5" goto status
if "%choice%"=="6" goto exit
goto menu

:minimal
echo.
echo MINIMAL MODE: Keeping only essential extensions...
echo Disabling ALL non-essential extensions...

REM Disable all except core essentials
code --disable-extension eamodio.gitlens
code --disable-extension esbenp.prettier-vscode
code --disable-extension github.vscode-github-actions
code --disable-extension github.vscode-pull-request-github
code --disable-extension google.geminicodeassist
code --disable-extension hbenl.vscode-test-explorer
code --disable-extension littlefoxteam.vscode-python-test-adapter
code --disable-extension mechatroner.rainbow-csv
code --disable-extension ms-azuretools.vscode-docker
code --disable-extension ms-toolsai.jupyter
code --disable-extension ms-toolsai.jupyter-keymap
code --disable-extension ms-toolsai.jupyter-renderers
code --disable-extension ms-toolsai.vscode-jupyter-cell-tags
code --disable-extension ms-toolsai.vscode-jupyter-slideshow
code --disable-extension ms-vscode-remote.remote-containers
code --disable-extension ms-vscode.powershell
code --disable-extension ms-vscode.test-adapter-converter
code --disable-extension ms-vscode.vscode-speech
code --disable-extension pkief.material-icon-theme
code --disable-extension wayou.vscode-todo-highlight
code --disable-extension anysphere.remote-containers

echo MINIMAL optimization complete!
echo Only keeping: Copilot, Python, Pylance, Debugpy, YAML, Markdown
goto end

:moderate
echo.
echo MODERATE MODE: Disabling heavy/redundant extensions...

code --disable-extension ms-toolsai.jupyter
code --disable-extension ms-toolsai.jupyter-keymap
code --disable-extension ms-toolsai.jupyter-renderers
code --disable-extension ms-toolsai.vscode-jupyter-cell-tags
code --disable-extension ms-toolsai.vscode-jupyter-slideshow
code --disable-extension google.geminicodeassist
code --disable-extension hbenl.vscode-test-explorer
code --disable-extension littlefoxteam.vscode-python-test-adapter
code --disable-extension ms-vscode.test-adapter-converter
code --disable-extension anysphere.remote-containers
code --disable-extension ms-azuretools.vscode-docker
code --disable-extension ms-vscode-remote.remote-containers
code --disable-extension mechatroner.rainbow-csv
code --disable-extension ms-vscode.vscode-speech
code --disable-extension wayou.vscode-todo-highlight

echo MODERATE optimization complete!
echo Keeping Git, GitHub, and visual enhancements active
goto end

:selective
echo.
echo SELECTIVE MODE: Choose extensions to disable...
echo.
set /p disable_jupyter="Disable Jupyter extensions? (y/n): "
if /i "%disable_jupyter%"=="y" (
    code --disable-extension ms-toolsai.jupyter
    code --disable-extension ms-toolsai.jupyter-keymap
    code --disable-extension ms-toolsai.jupyter-renderers
    code --disable-extension ms-toolsai.vscode-jupyter-cell-tags
    code --disable-extension ms-toolsai.vscode-jupyter-slideshow
)

set /p disable_docker="Disable Docker/Container extensions? (y/n): "
if /i "%disable_docker%"=="y" (
    code --disable-extension anysphere.remote-containers
    code --disable-extension ms-azuretools.vscode-docker
    code --disable-extension ms-vscode-remote.remote-containers
)

set /p disable_gemini="Disable Google Gemini Code Assist? (y/n): "
if /i "%disable_gemini%"=="y" (
    code --disable-extension google.geminicodeassist
)

set /p disable_gitlens="Disable GitLens? (y/n): "
if /i "%disable_gitlens%"=="y" (
    code --disable-extension eamodio.gitlens
)

echo SELECTIVE optimization complete!
goto end

:revert
echo.
echo REVERTING: Re-enabling all extensions...

code --enable-extension eamodio.gitlens
code --enable-extension esbenp.prettier-vscode
code --enable-extension github.vscode-github-actions
code --enable-extension github.vscode-pull-request-github
code --enable-extension google.geminicodeassist
code --enable-extension hbenl.vscode-test-explorer
code --enable-extension littlefoxteam.vscode-python-test-adapter
code --enable-extension mechatroner.rainbow-csv
code --enable-extension ms-azuretools.vscode-docker
code --enable-extension ms-toolsai.jupyter
code --enable-extension ms-toolsai.jupyter-keymap
code --enable-extension ms-toolsai.jupyter-renderers
code --enable-extension ms-toolsai.vscode-jupyter-cell-tags
code --enable-extension ms-toolsai.vscode-jupyter-slideshow
code --enable-extension ms-vscode-remote.remote-containers
code --enable-extension ms-vscode.powershell
code --enable-extension ms-vscode.test-adapter-converter
code --enable-extension ms-vscode.vscode-speech
code --enable-extension pkief.material-icon-theme
code --enable-extension wayou.vscode-todo-highlight
code --enable-extension anysphere.remote-containers

echo All extensions re-enabled!
goto end

:status
echo.
echo Current VS Code extensions status:
code --list-extensions --show-versions
echo.
goto menu

:end
echo.
echo =====================================================
echo IMPORTANT: Restart VS Code for changes to take effect
echo =====================================================
echo.
pause
goto exit

:exit
