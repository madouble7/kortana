$env:PYTHONPATH = "backend"
& "c:\KOR-TANA\kortana\venv\Scripts\python.exe" -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000
