"""API router for recommendation engine endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....services.database import get_db_sync
from .. import schemas, services

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendation Engine"],
)


@router.post("/", response_model=schemas.RecommendationResponse)
def get_recommendations(
    request: schemas.RecommendationRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Get product recommendations for a user.
    
    Uses embedding-based similarity search to find products that match
    the user's query and preferences.
    
    - **user_id**: User identifier
    - **query**: Optional search query or context
    - **limit**: Maximum number of recommendations to return (1-50)
    
    Returns a list of recommended products with scores and reasoning.
    """
    service = services.RecommendationService(db=db)
    return service.get_recommendations(request)


@router.post("/preferences", response_model=schemas.UserPreferenceDisplay)
def create_user_preference(
    preference: schemas.UserPreferenceCreate,
    db: Session = Depends(get_db_sync)
):
    """
    Create or update user preferences.
    
    Preferences are used to personalize recommendations. They can include
    any key-value pairs such as:
    - favorite_categories: ["ELECTRONICS", "BOOKS"]
    - price_range: "medium"
    - interests: "technology, reading"
    """
    service = services.RecommendationService(db=db)
    return service.create_user_preference(preference)


@router.get("/preferences/{user_id}", response_model=schemas.UserPreferenceDisplay)
def get_user_preference(
    user_id: str,
    db: Session = Depends(get_db_sync)
):
    """
    Get user preferences by user ID.
    """
    service = services.RecommendationService(db=db)
    preference = service.get_user_preference(user_id)
    if not preference:
        raise HTTPException(status_code=404, detail="User preferences not found")
    return preference


@router.get("/history/{user_id}", response_model=list[schemas.RecommendationDisplay])
def get_user_recommendation_history(
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_sync)
):
    """
    Get recommendation history for a user.
    
    Returns past recommendations made for the specified user.
    """
    service = services.RecommendationService(db=db)
    return service.get_user_recommendation_history(user_id, skip=skip, limit=limit)


@router.get("/all", response_model=list[schemas.RecommendationDisplay])
def get_all_recommendations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_sync)
):
    """
    Get all recommendations with pagination.
    
    Useful for analytics and monitoring recommendation patterns.
    """
    service = services.RecommendationService(db=db)
    return service.get_all_recommendations(skip=skip, limit=limit)
