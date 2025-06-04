from sqlalchemy.orm import Session

from . import models


class MemoryCoreService:
    def __init__(self, db: Session):
        self.db = db

    def store_memory(self, title: str, content: str):
        db_memory = models.CoreMemory(title=title, content=content)
        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def retrieve_memory_by_id(self, memory_id: int):
        return (
            self.db.query(models.CoreMemory)
            .filter(models.CoreMemory.id == memory_id)
            .first()
        )
