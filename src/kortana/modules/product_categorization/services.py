"""Service for product categorization using AI."""
from sqlalchemy.orm import Session

from src.kortana.services.embedding_service import embedding_service
from src.kortana.llm_clients.factory import LLMClientFactory

from . import models, schemas


class CategorizationService:
    """Service for categorizing products using embeddings and LLM."""

    def __init__(self, db: Session):
        self.db = db
        self.llm_client = LLMClientFactory.create_client("openai")

    def categorize_product(
        self, request: schemas.ProductCategorizeRequest
    ) -> schemas.ProductCategorizeResponse:
        """
        Categorize a product using AI.
        
        Uses LLM to determine product category based on name and description.
        """
        # Build the prompt for categorization
        text_to_categorize = f"Product Name: {request.name}"
        if request.description:
            text_to_categorize += f"\nDescription: {request.description}"

        # Get LLM to categorize
        prompt = f"""Analyze the following product and categorize it into ONE of these categories:
ELECTRONICS, FASHION, HOME, FOOD, BOOKS, SPORTS, HEALTH, AUTOMOTIVE, OTHER

{text_to_categorize}

Respond with ONLY the category name (one word) and a confidence score (0-1) and brief reasoning.
Format: CATEGORY|confidence|reasoning
Example: ELECTRONICS|0.95|This is clearly an electronic device based on the description."""

        response = self.llm_client.generate_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=100
        )

        # Parse the response
        try:
            parts = response.strip().split("|")
            category_str = parts[0].strip().upper()
            confidence = float(parts[1].strip()) if len(parts) > 1 else 0.8
            reasoning = parts[2].strip() if len(parts) > 2 else "AI categorization"

            # Map string to CategoryType enum
            category = models.CategoryType[category_str]
            
            return schemas.ProductCategorizeResponse(
                category=category,
                confidence_score=confidence,
                reasoning=reasoning
            )
        except (ValueError, KeyError, IndexError):
            # Default to OTHER if parsing fails
            return schemas.ProductCategorizeResponse(
                category=models.CategoryType.OTHER,
                confidence_score=0.5,
                reasoning="Unable to determine specific category"
            )

    def create_product(
        self, product_create: schemas.ProductCreate
    ) -> models.Product:
        """Create a new product with optional auto-categorization."""
        # Generate embedding for the product
        text_to_embed = product_create.name
        if product_create.description:
            text_to_embed += f"\n{product_create.description}"

        generated_embedding = embedding_service.get_embedding_for_text(text_to_embed)

        # Auto-categorize if category not provided
        if product_create.category is None:
            categorization = self.categorize_product(
                schemas.ProductCategorizeRequest(
                    name=product_create.name,
                    description=product_create.description
                )
            )
            category = categorization.category
            confidence = categorization.confidence_score
        else:
            category = product_create.category
            confidence = 1.0

        # Create the product
        db_product = models.Product(
            name=product_create.name,
            description=product_create.description,
            category=category,
            confidence_score=confidence,
            embedding=generated_embedding,
            product_metadata=product_create.product_metadata
        )

        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def get_product_by_id(self, product_id: int) -> models.Product | None:
        """Retrieve a product by ID."""
        return (
            self.db.query(models.Product)
            .filter(models.Product.id == product_id)
            .first()
        )

    def get_all_products(
        self, skip: int = 0, limit: int = 100
    ) -> list[models.Product]:
        """Retrieve all products with pagination."""
        return (
            self.db.query(models.Product)
            .order_by(models.Product.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_products_by_category(
        self, category: models.CategoryType, skip: int = 0, limit: int = 100
    ) -> list[models.Product]:
        """Retrieve products by category."""
        return (
            self.db.query(models.Product)
            .filter(models.Product.category == category)
            .order_by(models.Product.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_product(
        self, product_id: int, product_update: schemas.ProductUpdate
    ) -> models.Product | None:
        """Update a product."""
        db_product = self.get_product_by_id(product_id)
        if not db_product:
            return None

        update_data = product_update.model_dump(exclude_unset=True)
        
        # Regenerate embedding if name or description changed
        if "name" in update_data or "description" in update_data:
            text_to_embed = update_data.get("name", db_product.name)
            description = update_data.get("description", db_product.description)
            if description:
                text_to_embed += f"\n{description}"
            update_data["embedding"] = embedding_service.get_embedding_for_text(text_to_embed)

        for key, value in update_data.items():
            setattr(db_product, key, value)

        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        db_product = self.get_product_by_id(product_id)
        if not db_product:
            return False

        self.db.delete(db_product)
        self.db.commit()
        return True
