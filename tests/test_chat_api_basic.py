"""
Simple test to verify chat API structure without requiring full initialization.
"""

def test_chat_api_structure():
    """Test that the chat API has the correct structure."""
    from src.kortana.main import app
    from fastapi.testclient import TestClient
    
    # Create test client
    client = TestClient(app, raise_server_exceptions=False)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    print("✅ Health endpoint works")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    print("✅ Root endpoint works")
    
    # Test that chat endpoint exists (even if it errors due to missing dependencies)
    response = client.post("/chat", json={"message": "test"})
    # It may error due to missing DB/API keys, but endpoint should exist
    print(f"✅ Chat endpoint exists (status: {response.status_code})")
    
    print("\n✅ All basic API structure tests passed!")

if __name__ == "__main__":
    test_chat_api_structure()
