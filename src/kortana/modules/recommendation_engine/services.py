"""Service for recommendation engine using embeddings and similarity search."""
import numpy as np
from sqlalchemy.orm import Session

from src.kortana.services.embedding_service import embedding_service
from src.kortana.modules.product_categorization.models import Product

from . import models, schemas


def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)


class RecommendationService:
    """Service for generating product recommendations using embeddings."""

    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(
        self, request: schemas.RecommendationRequest
    ) -> schemas.RecommendationResponse:
        """
        Generate product recommendations for a user.
        
        Uses embedding-based similarity search to find relevant products
        based on user preferences and query.
        """
        # Get or create user preferences
        user_pref = self._get_or_create_user_preference(request.user_id)

        # Generate query embedding
        query_text = request.query or "general products"
        if user_pref.preferences:
            # Incorporate user preferences into query
            pref_str = ", ".join([f"{k}: {v}" for k, v in user_pref.preferences.items()])
            query_text = f"{query_text}. User preferences: {pref_str}"

        query_embedding = embedding_service.get_embedding_for_text(query_text)

        # Find similar products using embeddings
        all_products = self.db.query(Product).filter(Product.embedding.isnot(None)).all()

        # Calculate similarities
        similarities = []
        for product in all_products:
            if product.embedding:
                similarity = cosine_similarity(query_embedding, product.embedding)
                similarities.append({
                    "product": product,
                    "score": similarity
                })

        # Sort by similarity score
        similarities.sort(key=lambda x: x["score"], reverse=True)

        # Get top recommendations
        top_recommendations = similarities[:request.limit]

        # Create recommendation items
        recommendation_items = []
        for item in top_recommendations:
            product = item["product"]
            score = float(item["score"])
            
            # Generate reasoning
            reasoning = f"Similarity score: {score:.3f}. Category: {product.category.value if product.category else 'uncategorized'}."
            
            recommendation_items.append(schemas.RecommendationItem(
                product_id=product.id,
                product_name=product.name,
                recommendation_score=score,
                reasoning=reasoning
            ))

            # Store recommendation in database
            db_recommendation = models.Recommendation(
                user_id=request.user_id,
                product_id=product.id,
                product_name=product.name,
                recommendation_score=score,
                reasoning=reasoning
            )
            self.db.add(db_recommendation)

        self.db.commit()

        return schemas.RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendation_items,
            query=request.query
        )

    def _get_or_create_user_preference(self, user_id: str) -> models.UserPreference:
        """Get or create user preference."""
        user_pref = (
            self.db.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )

        if not user_pref:
            user_pref = models.UserPreference(
                user_id=user_id,
                preferences={},
                embedding=None
            )
            self.db.add(user_pref)
            self.db.commit()
            self.db.refresh(user_pref)

        return user_pref

    def create_user_preference(
        self, pref_create: schemas.UserPreferenceCreate
    ) -> models.UserPreference:
        """Create or update user preference."""
        # Check if preference already exists
        existing = (
            self.db.query(models.UserPreference)
            .filter(models.UserPreference.user_id == pref_create.user_id)
            .first()
        )

        if existing:
            # Update existing
            existing.preferences = pref_create.preferences
            
            # Generate embedding from preferences
            if pref_create.preferences:
                pref_text = ", ".join([f"{k}: {v}" for k, v in pref_create.preferences.items()])
                existing.embedding = embedding_service.get_embedding_for_text(pref_text)
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new
            embedding = None
            if pref_create.preferences:
                pref_text = ", ".join([f"{k}: {v}" for k, v in pref_create.preferences.items()])
                embedding = embedding_service.get_embedding_for_text(pref_text)

            db_pref = models.UserPreference(
                user_id=pref_create.user_id,
                preferences=pref_create.preferences,
                embedding=embedding
            )
            self.db.add(db_pref)
            self.db.commit()
            self.db.refresh(db_pref)
            return db_pref

    def get_user_preference(self, user_id: str) -> models.UserPreference | None:
        """Get user preference by user_id."""
        return (
            self.db.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )

    def get_user_recommendation_history(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> list[models.Recommendation]:
        """Get recommendation history for a user."""
        return (
            self.db.query(models.Recommendation)
            .filter(models.Recommendation.user_id == user_id)
            .order_by(models.Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_recommendations(
        self, skip: int = 0, limit: int = 100
    ) -> list[models.Recommendation]:
        """Get all recommendations with pagination."""
        return (
            self.db.query(models.Recommendation)
            .order_by(models.Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
