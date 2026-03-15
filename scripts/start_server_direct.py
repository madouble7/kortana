#!/usr/bin/env python3
"""
Direct Server Launch for Genesis Protocol
Manual FastAPI server startup for autonomous testing
"""


def start_server():
    """Start the FastAPI server directly"""
    print("🚀 GENESIS PROTOCOL - DIRECT SERVER LAUNCH")
    print("=" * 50)
    print()

    try:
        import uvicorn

        from kortana.main import app

        print("✅ FastAPI app imported successfully")
        print("🔄 Starting server on http://127.0.0.1:8000...")
        print()
        print("🎯 Once running, use assign_genesis_goal.py to submit the first goal")
        print("📊 Monitor autonomous activity in real-time")
        print()
        print("Press Ctrl+C to stop...")
        print("-" * 50)

        # Start the server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False,  # Disable reload for stability during autonomous ops
        )

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you're in the project root directory")
        print("2. Check that src/kortana/main.py exists")
        print("3. Verify uvicorn is installed: pip install uvicorn")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    start_server()
