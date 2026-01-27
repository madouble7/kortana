# src/kortana/api/routers/memory_router.py
import traceback  # Import the traceback module

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from kortana.modules.memory_core import schemas, services
from kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/memories",
    tags=["Memory Core"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/", response_model=schemas.CoreMemoryDisplay, status_code=status.HTTP_201_CREATED
)
def create_new_memory(
    memory_in: schemas.CoreMemoryCreate, db: Session = Depends(get_db_sync)
):
    """
    Create a new core memory for Kor'tana.
    Includes enhanced error handling to diagnose 500 errors.
    """
    try:
        service = services.MemoryCoreService(db)
        db_memory = service.create_memory(memory_create=memory_in)
        return db_memory
    except Exception as e:
        # This is our diagnostic block.
        # It will catch ANY exception that occurs inside the endpoint logic.
        print(f"ERROR in create_new_memory: {e}")
        # We raise an HTTPException to send a detailed error back to the client.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc().splitlines(),
            },
        )


@router.get("/{memory_id}", response_model=schemas.CoreMemoryDisplay)
def read_memory(memory_id: int, db: Session = Depends(get_db_sync)):
    """
    Retrieve a specific memory by its ID.
    """
    try:
        service = services.MemoryCoreService(db)
        db_memory = service.get_memory_by_id(memory_id=memory_id)
        if db_memory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )
        return db_memory
    except Exception as e:
        print(f"ERROR in read_memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc().splitlines(),
            },
        )


@router.get("/", response_model=list[schemas.CoreMemoryDisplay])
def read_all_memories(
    skip: int = 0, limit: int = 20, db: Session = Depends(get_db_sync)
):
    """
    Retrieve a list of all memories with pagination.
    """
    try:
        service = services.MemoryCoreService(db)
        memories = service.get_all_memories(skip=skip, limit=limit)
        return memories
    except Exception as e:
        print(f"ERROR in read_all_memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc().splitlines(),
            },
        )


# --- Other endpoints (PUT, DELETE) can be updated similarly if needed ---


@router.put("/{memory_id}", response_model=schemas.CoreMemoryDisplay)
def update_existing_memory(
    memory_id: int,
    memory_in: schemas.CoreMemoryUpdate,
    db: Session = Depends(get_db_sync),
):
    # ... (implementation)
    pass


@router.delete("/{memory_id}", response_model=schemas.CoreMemoryDisplay)
def delete_existing_memory(memory_id: int, db: Session = Depends(get_db_sync)):
    # ... (implementation)
    pass
