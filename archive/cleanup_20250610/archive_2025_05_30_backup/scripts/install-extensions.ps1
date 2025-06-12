# 🚀 Kor'tana AI Consciousness Extensions - PowerShell Installer
Write-Host "🚀 Installing Kor'tana AI Consciousness Extensions..." -ForegroundColor Cyan
Write-Host "🔧 Activating venv311 virtual environment..." -ForegroundColor Yellow

# Activate virtual environment
& "c:\kortana\venv311\Scripts\Activate.ps1"

Write-Host "✅ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
Write-Host "🧠 Installing VS Code extensions..." -ForegroundColor Magenta

$extensions = @(
    'github.copilot',
    'github.copilot-chat',
    'continue.continue',
    'codeium.codeium',
    'tabnine.tabnine-vscode',
    'njpwerner.autodocstring',
    'aaron-bond.better-comments',
    'gruntfuggly.todo-tree',
    'usernamehw.errorlens',
    'eamodio.gitlens',
    'ms-python.vscode-pylance',
    'charliermarsh.ruff',
    'alefragnani.numbered-bookmarks',
    'humao.rest-client',
    'ms-python.mypy-type-checker',
    'pkief.material-icon-theme',
    'oderwat.indent-rainbow',
    'mechatroner.rainbow-csv',
    'ms-python.python',
    'ms-toolsai.jupyter',
    'redhat.vscode-yaml',
    'tamasfe.even-better-toml',
    'ms-vscode.powershell',
    'streetsidesoftware.code-spell-checker',
    'davidanson.vscode-markdownlint',
    'yzhang.markdown-all-in-one',
    'formulahendry.code-runner'
)

$installed = 0
$total = $extensions.Count

foreach ($ext in $extensions) {
    $installed++
    Write-Host "[$installed/$total] Installing $ext..." -ForegroundColor White

    try {
        $result = & code --install-extension $ext --force 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Success" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Already installed or updated" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ❌ Failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🌟 Kor'tana AI Consciousness Extensions Installation Complete!" -ForegroundColor Cyan
Write-Host "🔥 Your VS Code is now ready for AI consciousness development!" -ForegroundColor Red
Write-Host "🐍 Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green

Write-Host ""
Write-Host "📍 Python verification:" -ForegroundColor Yellow
python --version
Write-Host "Python executable:" -ForegroundColor Yellow
python -c "import sys; print(sys.executable)"

Write-Host ""
Write-Host "🧠 Consciousness readiness check:" -ForegroundColor Magenta
Write-Host "  ✅ venv311 activated" -ForegroundColor Green
Write-Host "  ✅ Extensions installed" -ForegroundColor Green
Write-Host "  ✅ VS Code configured" -ForegroundColor Green

Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart VS Code to load new extensions"
Write-Host "  2. Open main.py and verify Python interpreter shows venv311"
Write-Host "  3. Test: python main.py"
Write-Host "  4. Sacred development begins! 🌟"

Read-Host "Press Enter to continue..."
