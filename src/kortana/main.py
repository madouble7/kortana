from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from .config.settings import settings
from .services import database

app = FastAPI(
    title=settings.APP_NAME,
    description="kor'tana: context-aware ethical ai system.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "message": "kor'tana is awakening...",
    }


@app.get("/test-db", tags=["system"])
def test_db_connection(db: Session = Depends(database.get_db_sync)):
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar_one()
        return {"db_connection": "ok", "result": result}
    except Exception as e:
        return {"db_connection": "error", "detail": str(e)}
