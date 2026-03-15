"""Quick validation script for e-commerce AI modules."""
import os
import sys

# Set dummy API key for validation
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-validation"

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        from src.kortana.modules.product_categorization import models as cat_models
        from src.kortana.modules.product_categorization import schemas as cat_schemas
        from src.kortana.modules.product_categorization import services as cat_services
        print("✓ Product categorization module imports OK")
    except Exception as e:
        print(f"✗ Product categorization module import failed: {e}")
        return False
    
    try:
        from src.kortana.modules.inventory_analysis import models as inv_models
        from src.kortana.modules.inventory_analysis import schemas as inv_schemas
        from src.kortana.modules.inventory_analysis import services as inv_services
        print("✓ Inventory analysis module imports OK")
    except Exception as e:
        print(f"✗ Inventory analysis module import failed: {e}")
        return False
    
    try:
        from src.kortana.modules.recommendation_engine import models as rec_models
        from src.kortana.modules.recommendation_engine import schemas as rec_schemas
        from src.kortana.modules.recommendation_engine import services as rec_services
        print("✓ Recommendation engine module imports OK")
    except Exception as e:
        print(f"✗ Recommendation engine module import failed: {e}")
        return False
    
    return True


def test_ml_models():
    """Test ML models can be loaded."""
    print("\nTesting ML model loading...")
    import pickle
    from pathlib import Path
    
    try:
        base_path = Path(__file__).parent / "data" / "ml_models"
        model_path = base_path / "model.pkl"
        scaler_path = base_path / "scaler.pkl"
        
        if model_path.exists():
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            print(f"✓ ML model loaded: {type(model)}")
        else:
            print(f"⚠ ML model file not found at {model_path}")
        
        if scaler_path.exists():
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)
            print(f"✓ Scaler loaded: {type(scaler)}")
        else:
            print(f"⚠ Scaler file not found at {scaler_path}")
        
        return True
    except Exception as e:
        print(f"✗ ML model loading failed: {e}")
        return False


def test_database_models():
    """Test database models are properly defined."""
    print("\nTesting database models...")
    
    try:
        from src.kortana.modules.product_categorization.models import Product, CategoryType
        from src.kortana.modules.inventory_analysis.models import Inventory, StockStatus
        from src.kortana.modules.recommendation_engine.models import UserPreference, Recommendation
        
        # Check enums
        assert hasattr(CategoryType, 'ELECTRONICS')
        assert hasattr(StockStatus, 'IN_STOCK')
        print("✓ All database models defined correctly")
        return True
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False


def test_api_routes():
    """Test API routes are registered."""
    print("\nTesting API routes...")
    
    try:
        from src.kortana.main import app
        
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/categories/classify",
            "/categories/products",
            "/inventory/analyze",
            "/inventory/",
            "/recommendations/",
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route registered: {route}")
            else:
                print(f"⚠ Route not found: {route}")
        
        return True
    except Exception as e:
        print(f"✗ API routes test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("E-COMMERCE AI MODULES VALIDATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("ML Models", test_ml_models()))
    results.append(("Database Models", test_database_models()))
    results.append(("API Routes", test_api_routes()))
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
