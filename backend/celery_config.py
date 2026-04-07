"""Compatibility shim that re-exports the canonical Celery application from ``src.kortana.celery_app``."""

from src.kortana.celery_app import app

if __name__ == "__main__":
    app.start()
