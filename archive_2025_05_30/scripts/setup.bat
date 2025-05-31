@echo off
echo Cleaning up old virtual environment...
if exist venv311 rmdir /s /q venv311

echo Creating new virtual environment...
python -m venv venv311

echo Installing requirements...
call venv311\Scripts\activate.bat
pip install google-generativeai==0.8.5 python-dotenv==1.0.1

echo Virtual environment setup complete.
echo You can now run: python test_genai.py
