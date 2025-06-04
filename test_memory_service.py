#!/usr/bin/env python3
"""
Test the memory core service directly
"""
import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from kortana.modules.memory_core.services import MemoryCoreService
from kortana.services.database import SyncSessionLocal

def test_memory_service():
    """Test the memory core service."""
    print("=== Memory Core Service Test ===")
    
    try:
        # Test database connection
        session = SyncSessionLocal()
        print("✅ Database session created successfully")        # Test memory service
        memory_service = MemoryCoreService(session)
        print("✅ MemoryCoreService initialized successfully")
        
        # Test storing a memory
        memory = memory_service.store_memory(
            title="Test Memory",
            content="This is a test memory to validate the service works correctly."
        )
        memory_id = memory.id
        print(f"✅ Memory stored successfully with ID: {memory_id}")
        
        # Test retrieving the memory
        retrieved_memory = memory_service.retrieve_memory_by_id(memory_id)
        if retrieved_memory:
            print(f"✅ Memory retrieved successfully:")
            print(f"   Title: {retrieved_memory.title}")
            print(f"   Content: {retrieved_memory.content}")
            print(f"   Created: {retrieved_memory.created_at}")
        else:
            print("❌ Failed to retrieve memory")
            return False

        session.close()
        print("✅ Database session closed successfully")
        return True

    except Exception as e:
        print(f"❌ Error testing memory service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_memory_service()
    print("\n=== Test Complete ===")
    if success:
        print("🎉 Memory service test passed!")
    else:
        print("❌ Memory service test failed.")
