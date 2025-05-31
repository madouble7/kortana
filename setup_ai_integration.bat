@echo off
REM Kor'tana AI Integration Setup
REM =============================

echo.
echo ==========================================
echo  KOR'TANA AI INTEGRATION SETUP
echo ==========================================
echo.

echo This script helps you configure AI integration for full autonomous power!
echo.

echo Step 1: Choose your AI integration level
echo ========================================
echo.
echo 1. Basic Setup    - Gemini 2.0 Flash (recommended)
echo 2. Multi-Model    - Gemini + Claude + GPT (advanced)
echo 3. Custom Setup   - Your own configuration
echo 4. Test Current   - Test existing configuration
echo.

set /p ai_choice="Enter choice (1-4): "

if "%ai_choice%"=="1" goto gemini_setup
if "%ai_choice%"=="2" goto multi_model_setup
if "%ai_choice%"=="3" goto custom_setup
if "%ai_choice%"=="4" goto test_current
echo Invalid choice. Exiting.
goto end

:gemini_setup
echo.
echo ========================================
echo  GEMINI 2.0 FLASH SETUP
echo ========================================
echo.

echo To get your Gemini API key:
echo 1. Go to: https://makersuite.google.com/app/apikey
echo 2. Sign in with your Google account
echo 3. Click "Create API key"
echo 4. Copy the key
echo.

set /p has_key="Do you have your Gemini API key? (y/n): "

if /i "%has_key%"=="y" (
    set /p gemini_key="Enter your Gemini API key: "
    echo.
    echo Setting environment variable...
    setx GEMINI_API_KEY "%gemini_key%" >nul
    echo [OK] GEMINI_API_KEY configured!
    echo.
    echo Testing configuration...
    call venv311\Scripts\activate.bat
    python -c "import os; print('API Key set:', 'GEMINI_API_KEY' in os.environ)"
    python relays\relay.py --summarize
) else (
    echo.
    echo No problem! Get your key when ready and run:
    echo   set GEMINI_API_KEY=your_key_here
    echo.
    echo The system will work in mock mode until then.
)
goto end

:multi_model_setup
echo.
echo ========================================
echo  MULTI-MODEL SETUP (ADVANCED)
echo ========================================
echo.

echo Configure multiple AI models for maximum capability:
echo.
echo Required API keys:
echo - Gemini 2.0 Flash: Context management and summarization
echo - Claude (Anthropic): Strategic analysis and reasoning
echo - GPT (OpenAI): Creative tasks and general assistance
echo.

echo This requires separate API keys from each provider.
echo Recommended for enterprise use or advanced experimentation.
echo.

echo To set up multi-model:
echo 1. Get API keys from each provider
echo 2. Set environment variables:
echo    set GEMINI_API_KEY=your_gemini_key
echo    set ANTHROPIC_API_KEY=your_claude_key
echo    set OPENAI_API_KEY=your_openai_key
echo 3. Run: python setup_multi_model.py
echo.

echo [INFO] Multi-model setup requires additional configuration.
echo Start with basic Gemini setup first.
goto end

:custom_setup
echo.
echo ========================================
echo  CUSTOM AI SETUP
echo ========================================
echo.

echo For custom AI integration:
echo.
echo 1. Edit relays\relay.py
echo 2. Add your preferred AI model
echo 3. Update the summarize_with_gemini() function
echo 4. Configure authentication as needed
echo.

echo Example integrations:
echo - Local models (Ollama, LM Studio)
echo - Cloud APIs (Azure OpenAI, AWS Bedrock)
echo - Custom endpoints
echo.

echo [INFO] Custom setup requires Python programming.
echo Documentation: README_PRODUCTION.md
goto end

:test_current
echo.
echo ========================================
echo  TESTING CURRENT CONFIGURATION
echo ========================================
echo.

call venv311\Scripts\activate.bat

echo Testing Gemini integration...
python -c "
import os
try:
    import google.generativeai as genai
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print('[OK] Gemini API key found')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print('[OK] Gemini model initialized')
        print('[OK] Full AI integration active!')
    else:
        print('[INFO] No API key - running in mock mode')
except ImportError:
    print('[ERROR] google-generativeai not installed')
except Exception as e:
    print(f'[ERROR] Configuration issue: {e}')
"

echo.
echo Testing relay system with current configuration...
python relays\relay.py --summarize

echo.
echo Testing complete!
goto end

:end
echo.
echo ========================================
echo  AI INTEGRATION SUMMARY
echo ========================================
echo.

echo Current status:
call venv311\Scripts\activate.bat
python -c "
import os
has_gemini = 'GEMINI_API_KEY' in os.environ
print(f'Gemini API Key: {'Configured' if has_gemini else 'Not set'}')
print(f'Integration Level: {'Full AI' if has_gemini else 'Mock Mode'}')
"

echo.
echo To activate full AI integration:
echo   1. Get Gemini API key from https://makersuite.google.com/app/apikey
echo   2. Run: set GEMINI_API_KEY=your_key_here
echo   3. Test: python relays\relay.py --summarize
echo.

echo Your autonomous system is ready to run with or without AI integration!
echo Run: automation_control.bat
echo.
pause
