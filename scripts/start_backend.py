#!/usr/bin/env python3
"""
Start the Kor'tana FastAPI Backend Server
"""

import subprocess
import sys
import time
from pathlib import Path

import requests

# Define project root and log directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
UVICORN_LOG_FILE = LOGS_DIR / "uvicorn_server.log"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)


def check_server_status(retries=10, delay=3):
    """Check if the backend server is running by querying the /health endpoint."""
    for i in range(retries):
        try:
            response = requests.get('http://localhost:8000/health', timeout=2)
            if response.status_code == 200:
                print(f"INFO: Health check attempt {i+1}/{retries} successful.")
                return True
            else:
                print(f"INFO: Health check attempt {i+1}/{retries} failed with status {response.status_code}.")
        except requests.ConnectionError:
            print(f"INFO: Health check attempt {i+1}/{retries} failed (ConnectionError). Server not yet available.")
        except requests.Timeout:
            print(f"INFO: Health check attempt {i+1}/{retries} failed (Timeout).")
        except Exception as e:
            print(f"INFO: Health check attempt {i+1}/{retries} failed ({type(e).__name__}: {e}).")

        if i < retries - 1:
            print(f"INFO: Waiting {delay} seconds before next health check...")
            time.sleep(delay)
    return False


def start_backend_server():
    """Start the FastAPI backend server with enhanced logging and health checks."""
    print("🚀 STARTING KOR'TANA BACKEND SERVER")
    print("=" * 50)

    if check_server_status(retries=1, delay=1): # Quick check if already running
        print("✅ Backend server already running at http://localhost:8000")
        return True

    print(f"📋 Starting FastAPI server... Uvicorn logs will be at: {UVICORN_LOG_FILE}")
    try:
        with open(UVICORN_LOG_FILE, 'wb') as uvicorn_log: # Open in binary mode for stdout/stderr
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "src.kortana.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], cwd=str(PROJECT_ROOT), stdout=uvicorn_log, stderr=subprocess.STDOUT)

        print("⏳ Waiting for server to initialize and become healthy (up to 30 seconds)...")
        # Improved health check loop
        if check_server_status(retries=10, delay=3): # More robust check
            print("✅ Backend server started successfully and is healthy!")
            print("🌐 Server running at: http://localhost:8000")
            print("📚 API Documentation: http://localhost:8000/docs")
            print(f"🪵 Uvicorn logs: {UVICORN_LOG_FILE}")
            return True
        else:
            print("❌ Server failed to start properly or become healthy after multiple checks.")
            print(f"🪵 Check Uvicorn logs for details: {UVICORN_LOG_FILE}")
            # Attempt to terminate the process if it started but isn't healthy
            if 'process' in locals() and process.poll() is None:
                print("INFO: Terminating unresponsive server process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("INFO: Server process terminated.")
            return False

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if start_backend_server():
        sys.exit(0)
    else:
        sys.exit(1)
