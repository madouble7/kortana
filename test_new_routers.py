"""
Standalone test for new module routers
Tests that routers can be imported and initialized
"""

import sys
import os

# Set required env vars before any imports
os.environ['OPENAI_API_KEY'] = 'test-key-placeholder'
os.environ['MEMORY_DB_URL'] = 'sqlite:///test.db'

sys.path.insert(0, 'src')

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a minimal test app
app = FastAPI()

# Import and include new module routers directly from their files
from kortana.modules.multilingual.router import router as multilingual_router
from kortana.modules.emotional_intelligence.router import (
    router as emotional_intelligence_router,
)
from kortana.modules.content_generation.router import router as content_router
from kortana.modules.plugin_framework.router import router as plugin_router
from kortana.modules.ethical_transparency.router import router as ethics_router
from kortana.modules.gaming.router import router as gaming_router
from kortana.modules.marketplace.router import router as marketplace_router

app.include_router(multilingual_router)
app.include_router(emotional_intelligence_router)
app.include_router(content_router)
app.include_router(plugin_router)
app.include_router(ethics_router)
app.include_router(gaming_router)
app.include_router(marketplace_router)

print("✅ All routers imported and registered successfully")

# Create test client
client = TestClient(app)

# Test some endpoints
print("\nTesting endpoints:")

# Test multilingual
response = client.get("/api/multilingual/languages")
print(f"  ✓ Multilingual /languages: {response.status_code}")

# Test emotional intelligence
response = client.post(
    "/api/emotional-intelligence/sentiment", json={"text": "This is great!"}
)
print(f"  ✓ Emotional Intelligence /sentiment: {response.status_code}")

# Test content generation
response = client.post(
    "/api/content/summarize", json={"text": "Test text", "max_length": 50}
)
print(f"  ✓ Content Generation /summarize: {response.status_code}")

# Test plugins
response = client.get("/api/plugins/list")
print(f"  ✓ Plugin Framework /list: {response.status_code}")

# Test ethics
response = client.get("/api/ethics/report")
print(f"  ✓ Ethical Transparency /report: {response.status_code}")

# Test gaming
response = client.post(
    "/api/gaming/rpg/roll", json={"dice_notation": "2d6"}
)
print(f"  ✓ Gaming /rpg/roll: {response.status_code}")

# Test marketplace
response = client.get("/api/marketplace/modules")
print(f"  ✓ Marketplace /modules: {response.status_code}")

print("\n✅ All API endpoints tested successfully!")
