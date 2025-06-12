@echo off
echo ========================================
echo    KOR'TANA LOBECHAT SETUP SCRIPT
echo ========================================
echo.

echo [1/5] Navigating to LobeChat directory...
cd /d "c:\project-kortana\lobechat-frontend"
if errorlevel 1 (
    echo ERROR: LobeChat directory not found!
    pause
    exit /b 1
)

echo [2/5] Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo [3/5] Setting up environment configuration...
if not exist ".env.local" (
    copy ".env.example" ".env.local"
    echo Environment file created: .env.local
) else (
    echo Environment file already exists: .env.local
)

echo [4/5] Creating Kor'tana API integration directory...
if not exist "src\libs\agent-runtime\kortana" (
    mkdir "src\libs\agent-runtime\kortana"
)

echo [5/5] Setup complete!
echo.
echo ========================================
echo           NEXT STEPS:
echo ========================================
echo 1. Edit .env.local with your API keys
echo 2. Configure Kor'tana backend URL
echo 3. Run: npm run dev
echo 4. Visit: http://localhost:3000
echo ========================================
echo.
pause
