"""API router for inventory analysis endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....services.database import get_db_sync
from .. import schemas, services
from ..models import StockStatus

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Analysis"],
)


@router.post("/analyze", response_model=schemas.InventoryAnalysisResponse)
def analyze_inventory(
    request: schemas.InventoryAnalysisRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Analyze inventory using financial metrics and ML model.
    
    Provides buy/don't buy recommendation based on:
    - P/E Ratio (Price to Earnings)
    - P/B Ratio (Price to Book)
    - D/E Ratio (Debt to Equity)
    - ROE (Return on Equity)
    - ROA (Return on Assets)
    
    Returns recommendation with confidence score and detailed analysis.
    """
    service = services.InventoryAnalysisService(db=db)
    return service.analyze_inventory(request)


@router.post("/", response_model=schemas.InventoryDisplay)
def create_inventory(
    inventory: schemas.InventoryCreate,
    db: Session = Depends(get_db_sync)
):
    """
    Create a new inventory entry.
    """
    service = services.InventoryAnalysisService(db=db)
    return service.create_inventory(inventory_create=inventory)


@router.post("/with-analysis", response_model=schemas.InventoryDisplay)
def create_inventory_with_analysis(
    request: schemas.InventoryAnalysisRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Create inventory entry with automatic financial analysis.
    
    This combines inventory creation with ML-based financial analysis.
    """
    service = services.InventoryAnalysisService(db=db)
    return service.create_inventory_with_analysis(request)


@router.get("/", response_model=list[schemas.InventoryDisplay])
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve all inventory entries with pagination.
    """
    service = services.InventoryAnalysisService(db=db)
    return service.get_all_inventory(skip=skip, limit=limit)


@router.get("/{inventory_id}", response_model=schemas.InventoryDisplay)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve a specific inventory entry by ID.
    """
    service = services.InventoryAnalysisService(db=db)
    inventory = service.get_inventory_by_id(inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory


@router.get("/status/{status}", response_model=list[schemas.InventoryDisplay])
def get_inventory_by_status(
    status: StockStatus,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve inventory by status.
    
    - **status**: Stock status (IN_STOCK, LOW_STOCK, OUT_OF_STOCK, OVERSTOCKED)
    """
    service = services.InventoryAnalysisService(db=db)
    return service.get_inventory_by_status(status=status, skip=skip, limit=limit)


@router.put("/{inventory_id}", response_model=schemas.InventoryDisplay)
def update_inventory(
    inventory_id: int,
    inventory_update: schemas.InventoryUpdate,
    db: Session = Depends(get_db_sync)
):
    """
    Update an inventory entry.
    """
    service = services.InventoryAnalysisService(db=db)
    updated_inventory = service.update_inventory(inventory_id, inventory_update)
    if not updated_inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return updated_inventory


@router.delete("/{inventory_id}")
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db_sync)
):
    """
    Delete an inventory entry.
    """
    service = services.InventoryAnalysisService(db=db)
    success = service.delete_inventory(inventory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return {"message": "Inventory deleted successfully"}
