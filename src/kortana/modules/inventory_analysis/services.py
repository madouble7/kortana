"""Service for inventory analysis using ML models from stock repository."""
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from . import models, schemas


class InventoryAnalysisService:
    """Service for analyzing inventory using financial metrics and ML model."""

    # Correlation matrix from stock repository
    CORRELATION_MATRIX = {
        "P/E Ratio": {"P/E Ratio": 1.0, "P/B Ratio": 0.0045, "D/E Ratio": -0.0035, "ROE": -0.0178, "ROA": -0.0105},
        "P/B Ratio": {"P/E Ratio": 0.0045, "P/B Ratio": 1.0, "D/E Ratio": 0.8175, "ROE": 0.0281, "ROA": 0.0153},
        "D/E Ratio": {"P/E Ratio": -0.0035, "P/B Ratio": 0.8175, "D/E Ratio": 1.0, "ROE": 0.0678, "ROA": -0.0069},
        "ROE": {"P/E Ratio": -0.0178, "P/B Ratio": 0.0281, "D/E Ratio": 0.0678, "ROE": 1.0, "ROA": 0.0771},
        "ROA": {"P/E Ratio": -0.0105, "P/B Ratio": 0.0153, "D/E Ratio": -0.0069, "ROE": 0.0771, "ROA": 1.0}
    }

    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.scaler = None
        self._load_models()

    def _load_models(self):
        """Load the pre-trained ML models."""
        try:
            # Find the models directory
            base_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "ml_models"
            model_path = base_path / "model.pkl"
            scaler_path = base_path / "scaler.pkl"

            if model_path.exists():
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
            
            if scaler_path.exists():
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load ML models: {e}")
            # Models will remain None, and fallback logic will be used

    def _adjust_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Adjust features based on correlation matrix.
        
        This is the same adjustment logic used in the stock repository.
        """
        adjusted = features.copy()
        for col in features.columns:
            adjustment = sum(
                features[other] * self.CORRELATION_MATRIX[col].get(other, 0)
                for other in features.columns
            )
            adjusted[col] = features[col] + adjustment
        return adjusted

    def analyze_inventory(
        self, request: schemas.InventoryAnalysisRequest
    ) -> schemas.InventoryAnalysisResponse:
        """
        Analyze inventory using financial metrics and ML model.
        
        Uses the trained XGBoost model from stock repository to provide
        buy/don't buy recommendations based on financial ratios.
        """
        # Create features dataframe
        features = pd.DataFrame([{
            "P/E Ratio": request.pe_ratio,
            "P/B Ratio": request.pb_ratio,
            "D/E Ratio": request.de_ratio,
            "ROE": request.roe,
            "ROA": request.roa
        }])

        if self.model is None or self.scaler is None:
            # Fallback: simple heuristic-based analysis
            return self._fallback_analysis(request)

        # Apply correlation-based adjustment
        adjusted_features = self._adjust_features(features)

        # Scale features
        scaled_features = self.scaler.transform(adjusted_features)

        # Make prediction
        prediction = self.model.predict(scaled_features)[0]
        prediction_proba = self.model.predict_proba(scaled_features)[0]

        # Determine recommendation
        recommendation = "Buy" if prediction == 1 else "Do not buy"
        confidence = prediction_proba[1] if prediction == 1 else prediction_proba[0]

        # Generate analysis text
        analysis = self._generate_analysis(request, recommendation, confidence)

        return schemas.InventoryAnalysisResponse(
            recommendation=recommendation,
            confidence_score=float(confidence),
            analysis=analysis
        )

    def _fallback_analysis(
        self, request: schemas.InventoryAnalysisRequest
    ) -> schemas.InventoryAnalysisResponse:
        """Fallback analysis using simple heuristics when ML model is unavailable."""
        # Simple scoring based on financial health
        score = 0.0
        
        # Good P/E ratio (lower is generally better, but not too low)
        if 10 <= request.pe_ratio <= 25:
            score += 0.2
        
        # Good P/B ratio (typically want < 3)
        if request.pb_ratio < 3:
            score += 0.2
        
        # Good D/E ratio (lower is better, typically want < 2)
        if request.de_ratio < 2:
            score += 0.2
        
        # Good ROE (higher is better, typically want > 10%)
        if request.roe > 10:
            score += 0.2
        
        # Good ROA (higher is better, typically want > 5%)
        if request.roa > 5:
            score += 0.2
        
        recommendation = "Buy" if score >= 0.6 else "Do not buy"
        
        return schemas.InventoryAnalysisResponse(
            recommendation=recommendation,
            confidence_score=score,
            analysis=f"Heuristic analysis: score {score:.2f}/1.00"
        )

    def _generate_analysis(
        self, request: schemas.InventoryAnalysisRequest, recommendation: str, confidence: float
    ) -> str:
        """Generate human-readable analysis text."""
        analysis_parts = [
            f"Based on financial metrics analysis:",
            f"- P/E Ratio: {request.pe_ratio:.2f}",
            f"- P/B Ratio: {request.pb_ratio:.2f}",
            f"- D/E Ratio: {request.de_ratio:.2f}",
            f"- ROE: {request.roe:.2f}%",
            f"- ROA: {request.roa:.2f}%",
            f"\nRecommendation: {recommendation} with {confidence*100:.2f}% confidence"
        ]
        return "\n".join(analysis_parts)

    def create_inventory(
        self, inventory_create: schemas.InventoryCreate
    ) -> models.Inventory:
        """Create a new inventory entry."""
        db_inventory = models.Inventory(
            product_name=inventory_create.product_name,
            sku=inventory_create.sku,
            quantity=inventory_create.quantity,
            status=inventory_create.status,
            metadata=inventory_create.metadata
        )

        self.db.add(db_inventory)
        self.db.commit()
        self.db.refresh(db_inventory)
        return db_inventory

    def create_inventory_with_analysis(
        self, request: schemas.InventoryAnalysisRequest
    ) -> models.Inventory:
        """Create inventory entry with financial analysis."""
        # Perform analysis
        analysis = self.analyze_inventory(request)

        # Create inventory with analysis results
        db_inventory = models.Inventory(
            product_name=request.product_name,
            quantity=0,  # Default quantity
            status=models.StockStatus.IN_STOCK,
            pe_ratio=request.pe_ratio,
            pb_ratio=request.pb_ratio,
            de_ratio=request.de_ratio,
            roe=request.roe,
            roa=request.roa,
            recommendation=analysis.recommendation,
            confidence_score=analysis.confidence_score,
            metadata={"analysis": analysis.analysis}
        )

        self.db.add(db_inventory)
        self.db.commit()
        self.db.refresh(db_inventory)
        return db_inventory

    def get_inventory_by_id(self, inventory_id: int) -> models.Inventory | None:
        """Retrieve inventory by ID."""
        return (
            self.db.query(models.Inventory)
            .filter(models.Inventory.id == inventory_id)
            .first()
        )

    def get_all_inventory(
        self, skip: int = 0, limit: int = 100
    ) -> list[models.Inventory]:
        """Retrieve all inventory with pagination."""
        return (
            self.db.query(models.Inventory)
            .order_by(models.Inventory.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_inventory_by_status(
        self, status: models.StockStatus, skip: int = 0, limit: int = 100
    ) -> list[models.Inventory]:
        """Retrieve inventory by status."""
        return (
            self.db.query(models.Inventory)
            .filter(models.Inventory.status == status)
            .order_by(models.Inventory.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_inventory(
        self, inventory_id: int, inventory_update: schemas.InventoryUpdate
    ) -> models.Inventory | None:
        """Update inventory."""
        db_inventory = self.get_inventory_by_id(inventory_id)
        if not db_inventory:
            return None

        update_data = inventory_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_inventory, key, value)

        self.db.commit()
        self.db.refresh(db_inventory)
        return db_inventory

    def delete_inventory(self, inventory_id: int) -> bool:
        """Delete inventory."""
        db_inventory = self.get_inventory_by_id(inventory_id)
        if not db_inventory:
            return False

        self.db.delete(db_inventory)
        self.db.commit()
        return True
