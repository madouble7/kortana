"""Compatibility entrypoint that forwards to the canonical FastAPI app in ``src.kortana.main``."""

from src.kortana.main import app, create_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.kortana.main:app", host="0.0.0.0", port=8000, reload=True)
