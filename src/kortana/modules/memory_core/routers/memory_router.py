# src/kortana/modules/memory_core/routers/memory_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....services.database import get_db_sync  # Adjust path as needed

# Assuming these are in the parent directory of this routers module
from .. import schemas, services

router = APIRouter(
    prefix="/memories",
    tags=["Memory Core"],
)


@router.post("/", response_model=schemas.CoreMemoryDisplay)
def create_memory_endpoint(
    memory: schemas.CoreMemoryCreate, db: Session = Depends(get_db_sync)
):
    service = services.MemoryCoreService(db=db)
    return service.create_memory(memory_create=memory)


@router.get("/", response_model=list[schemas.CoreMemoryDisplay])
def read_memories_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db_sync)
):
    service = services.MemoryCoreService(db=db)
    memories = service.get_all_memories(skip=skip, limit=limit)
    return memories


@router.get("/{memory_id}", response_model=schemas.CoreMemoryDisplay)
def read_memory_endpoint(memory_id: int, db: Session = Depends(get_db_sync)):
    service = services.MemoryCoreService(db=db)
    db_memory = service.get_memory_by_id(memory_id=memory_id)
    if db_memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return db_memory


# Add other CRUD endpoints (update, delete) as needed based on blueprint/schemas
