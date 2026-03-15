"""API router for product categorization endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....services.database import get_db_sync
from .. import schemas, services
from ..models import CategoryType

router = APIRouter(
    prefix="/categories",
    tags=["Product Categorization"],
)


@router.post("/classify", response_model=schemas.ProductCategorizeResponse)
def classify_product(
    request: schemas.ProductCategorizeRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Classify a product into a category using AI.
    
    - **name**: Product name (required)
    - **description**: Product description (optional)
    
    Returns the predicted category, confidence score, and reasoning.
    """
    service = services.CategorizationService(db=db)
    return service.categorize_product(request)


@router.post("/products", response_model=schemas.ProductDisplay)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db_sync)
):
    """
    Create a new product with automatic categorization.
    
    If category is not provided, it will be automatically determined using AI.
    """
    service = services.CategorizationService(db=db)
    return service.create_product(product_create=product)


@router.get("/products", response_model=list[schemas.ProductDisplay])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve all products with pagination.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    service = services.CategorizationService(db=db)
    return service.get_all_products(skip=skip, limit=limit)


@router.get("/products/{product_id}", response_model=schemas.ProductDisplay)
def get_product(
    product_id: int,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve a specific product by ID.
    """
    service = services.CategorizationService(db=db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/category/{category}", response_model=list[schemas.ProductDisplay])
def get_products_by_category(
    category: CategoryType,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_sync)
):
    """
    Retrieve products by category.
    
    - **category**: Category to filter by (ELECTRONICS, FASHION, HOME, etc.)
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    service = services.CategorizationService(db=db)
    return service.get_products_by_category(category=category, skip=skip, limit=limit)


@router.put("/products/{product_id}", response_model=schemas.ProductDisplay)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db_sync)
):
    """
    Update a product.
    """
    service = services.CategorizationService(db=db)
    updated_product = service.update_product(product_id, product_update)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db_sync)
):
    """
    Delete a product.
    """
    service = services.CategorizationService(db=db)
    success = service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
