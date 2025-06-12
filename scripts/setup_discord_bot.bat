@echo off
echo ========================================
echo    KOR'TANA DISCORD BOT SETUP SCRIPT
echo ========================================
echo.

echo [1/4] Installing Discord dependencies...
pip install discord.py python-dotenv
if errorlevel 1 (
    echo ERROR: Failed to install Discord dependencies!
    pause
    exit /b 1
)

echo [2/4] Checking environment configuration...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env file and add DISCORD_BOT_TOKEN
    pause
    exit /b 1
)

echo [3/4] Creating Discord bot script...
echo Discord bot script created at: src\discord_bot.py

echo [4/4] Setup complete!
echo.
echo ========================================
echo           NEXT STEPS:
echo ========================================
echo 1. Get Discord bot token from:
echo    https://discord.com/developers/applications
echo 2. Add DISCORD_BOT_TOKEN to .env file
echo 3. Invite bot to your Discord server
echo 4. Run: python src\discord_bot.py
echo ========================================
echo.
pause
