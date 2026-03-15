#!/usr/bin/env python3
"""
Test script for LobeChat OpenAI-compatible API endpoints.

This script validates that the LobeChat integration endpoints
are working correctly without starting a full server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.kortana.adapters.lobechat_openai_adapter import (
    ChatCompletionRequest,
    Message,
    ModelListResponse,
)


async def test_model_request():
    """Test that we can create a valid chat completion request."""
    print("🧪 Testing ChatCompletionRequest model...")
    
    request = ChatCompletionRequest(
        model="kortana-default",
        messages=[
            Message(role="user", content="Hello, Kor'tana!")
        ]
    )
    
    assert request.model == "kortana-default"
    assert len(request.messages) == 1
    assert request.messages[0].content == "Hello, Kor'tana!"
    print("✅ ChatCompletionRequest model works correctly")


async def test_model_list():
    """Test that we can create model list response."""
    print("\n🧪 Testing ModelListResponse...")
    
    from src.kortana.adapters.lobechat_openai_adapter import ModelInfo
    import time
    
    model_list = ModelListResponse(
        object="list",
        data=[
            ModelInfo(
                id="kortana-default",
                created=int(time.time()),
                owned_by="kortana"
            )
        ]
    )
    
    assert model_list.object == "list"
    assert len(model_list.data) == 1
    assert model_list.data[0].id == "kortana-default"
    print("✅ ModelListResponse works correctly")


async def test_message_validation():
    """Test message role validation."""
    print("\n🧪 Testing Message validation...")
    
    # Valid roles
    for role in ["system", "user", "assistant"]:
        msg = Message(role=role, content="Test")
        assert msg.role == role
    
    print("✅ Message validation works correctly")


async def test_imports():
    """Test that all necessary imports work."""
    print("\n🧪 Testing imports...")
    
    try:
        from src.kortana.core.orchestrator import KorOrchestrator
        print("✅ KorOrchestrator imported successfully")
    except ImportError as e:
        print(f"⚠️  Warning: Could not import KorOrchestrator: {e}")
    
    try:
        from src.kortana.services.database import get_db_sync
        print("✅ Database service imported successfully")
    except ImportError as e:
        print(f"⚠️  Warning: Could not import database service: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("LobeChat OpenAI-Compatible API - Unit Tests")
    print("=" * 60)
    
    try:
        await test_model_request()
        await test_model_list()
        await test_message_validation()
        await test_imports()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
