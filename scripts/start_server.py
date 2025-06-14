#!/usr/bin/env python3
"""
Start the FastAPI server for testing
"""

import os
import sys

import uvicorn

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    uvicorn.run("src.kortana.main:app", host="127.0.0.1", port=8001, reload=False)
