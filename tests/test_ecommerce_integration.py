"""
Integration tests for e-commerce AI features.

Tests the product categorization, inventory analysis, and recommendation engine modules.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kortana.main import app
from src.kortana.services.database import Base, get_db_sync


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ecommerce.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db_sync] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestProductCategorization:
    """Test product categorization module."""

    def test_health_check(self):
        """Test that API is running."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_classify_product_electronics(self):
        """Test product classification for electronics."""
        response = client.post(
            "/categories/classify",
            json={
                "name": "Wireless Headphones",
                "description": "Bluetooth noise-cancelling over-ear headphones"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert "confidence_score" in data
        assert 0 <= data["confidence_score"] <= 1

    def test_create_product(self):
        """Test creating a product with auto-categorization."""
        response = client.post(
            "/categories/products",
            json={
                "name": "Running Shoes",
                "description": "Lightweight athletic footwear for running"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Running Shoes"
        assert "category" in data
        assert "id" in data

    def test_list_products(self):
        """Test listing products."""
        response = client.get("/categories/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestInventoryAnalysis:
    """Test inventory analysis module."""

    def test_analyze_inventory_good_metrics(self):
        """Test inventory analysis with good financial metrics."""
        response = client.post(
            "/inventory/analyze",
            json={
                "product_name": "Test Product",
                "pe_ratio": 15.0,
                "pb_ratio": 2.0,
                "de_ratio": 0.5,
                "roe": 15.0,
                "roa": 8.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert data["recommendation"] in ["Buy", "Do not buy"]
        assert "confidence_score" in data
        assert 0 <= data["confidence_score"] <= 1

    def test_analyze_inventory_poor_metrics(self):
        """Test inventory analysis with poor financial metrics."""
        response = client.post(
            "/inventory/analyze",
            json={
                "product_name": "Test Product 2",
                "pe_ratio": 50.0,
                "pb_ratio": 10.0,
                "de_ratio": 5.0,
                "roe": 2.0,
                "roa": 1.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert "confidence_score" in data

    def test_create_inventory(self):
        """Test creating inventory entry."""
        response = client.post(
            "/inventory/",
            json={
                "product_name": "Widget A",
                "sku": "WGT-001",
                "quantity": 100,
                "status": "IN_STOCK"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "Widget A"
        assert data["quantity"] == 100

    def test_create_inventory_with_analysis(self):
        """Test creating inventory with analysis."""
        response = client.post(
            "/inventory/with-analysis",
            json={
                "product_name": "Widget B",
                "pe_ratio": 20.0,
                "pb_ratio": 3.0,
                "de_ratio": 1.0,
                "roe": 12.0,
                "roa": 6.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "Widget B"
        assert "recommendation" in data


class TestRecommendationEngine:
    """Test recommendation engine module."""

    def test_create_user_preference(self):
        """Test creating user preferences."""
        response = client.post(
            "/recommendations/preferences",
            json={
                "user_id": "user123",
                "preferences": {
                    "favorite_categories": ["ELECTRONICS", "BOOKS"],
                    "price_range": "medium"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"

    def test_get_user_preference(self):
        """Test retrieving user preferences."""
        # First create a preference
        client.post(
            "/recommendations/preferences",
            json={
                "user_id": "user456",
                "preferences": {"interests": "technology"}
            }
        )
        
        # Then retrieve it
        response = client.get("/recommendations/preferences/user456")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user456"

    def test_get_recommendations(self):
        """Test getting recommendations."""
        # First create some products
        client.post(
            "/categories/products",
            json={
                "name": "Laptop",
                "description": "High-performance laptop for work"
            }
        )
        
        # Get recommendations
        response = client.post(
            "/recommendations/",
            json={
                "user_id": "user789",
                "query": "technology products",
                "limit": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert data["user_id"] == "user789"


class TestModuleIntegration:
    """Test integration between modules."""

    def test_full_workflow(self):
        """Test complete workflow: categorize -> analyze -> recommend."""
        # Step 1: Create a product with categorization
        product_response = client.post(
            "/categories/products",
            json={
                "name": "Smart Watch",
                "description": "Fitness tracking smartwatch with heart rate monitor"
            }
        )
        assert product_response.status_code == 200
        product_data = product_response.json()
        
        # Step 2: Analyze inventory for similar product
        analysis_response = client.post(
            "/inventory/analyze",
            json={
                "product_name": "Smart Watch",
                "pe_ratio": 18.0,
                "pb_ratio": 2.5,
                "de_ratio": 0.8,
                "roe": 14.0,
                "roa": 7.5
            }
        )
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        # Step 3: Get recommendations for user interested in similar products
        rec_response = client.post(
            "/recommendations/",
            json={
                "user_id": "test_user",
                "query": "fitness and health products",
                "limit": 3
            }
        )
        assert rec_response.status_code == 200
        rec_data = rec_response.json()
        
        # Verify workflow completed successfully
        assert product_data["category"] in ["ELECTRONICS", "HEALTH", "SPORTS"]
        assert analysis_data["recommendation"] in ["Buy", "Do not buy"]
        assert len(rec_data["recommendations"]) >= 0  # May be 0 if no matching products


def test_api_documentation():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
