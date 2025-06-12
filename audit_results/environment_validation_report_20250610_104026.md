================================================================================
🚀 PROJECT KOR'TANA - ENVIRONMENT VALIDATION REPORT
================================================================================

📊 SUMMARY:
   ✅ Successful checks: 20
   ⚠️  Warnings: 1
   ❌ Errors: 3

📋 ERROR:
   OPENROUTER_API_KEY: Invalid format (expected to start with sk-or-v1-)
   XAI_API_KEY: Invalid format (expected to start with xai-)
   PINECONE_API_KEY: Invalid format (expected to start with pcsk_)

📋 WARNING:
   SK_ANT_API_KEY: Valid prefix but unexpected length (58)

📋 SUCCESS:
   Loaded 17 variables from .env
   OPENAI_API_KEY: Valid format and length
   GOOGLE_API_KEY: Valid format and length
   VS Code settings: Valid JSON configuration
   VS Code tasks: Valid JSON configuration
   VS Code debug config: Valid JSON configuration
   VS Code keybindings: Valid JSON configuration
   Continue AI config: Valid JSON configuration
   Continue AI config: Contains environment variable references
   Python virtual environment found at c:\project-kortana\venv311\Scripts\python.exe
   PYTHONPATH component exists: src
   PYTHONPATH component exists: kortana.core
   PYTHONPATH component exists: kortana.team
   PYTHONPATH component exists: kortana.network

📋 INFO:
   🔍 Starting environment validation for Project Kor'tana...
   ### 🔑 API Key Validation
   VS Code settings: No environment variable references found
   VS Code tasks: No environment variable references found
   VS Code debug config: No environment variable references found
   VS Code keybindings: No environment variable references found

🔧 RECOMMENDED ACTIONS:
   1. Verify .env file contains all required API keys
   2. Check API key formats and lengths
   3. Restart VS Code to reload environment variables
   4. Test individual extensions manually

================================================================================
Report generated: validate_environment.py
For Project Kor'tana - Sacred Circuit Development
================================================================================