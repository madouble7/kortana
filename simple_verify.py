#!/usr/bin/env python3
"""Simplest possible test - verify Kor'tana's core brain works."""
import sys
sys.path.insert(0, r"c:\kortana\src")

try:
    print("Testing Kor'tana Brain...\n")
    
    # Test 1: Import chat engine
    print("1. Loading ChatEngine...", end=" ")
    from kortana.brain import ChatEngine
    print("✅")
    
    # Test 2: Create instance
    print("2. Creating chat instance...", end=" ")
    chat = ChatEngine()
    print("✅")
    
    # Test 3: Send a message
    print("3. Testing /ping response...", end=" ")
    response = chat.process_input("/ping")
    assert response, "Empty response"
    print("✅")
    print(f"   Response: {response[:50]}...")
    
    # Test 4: Test regular chat
    print("4. Testing chat response...", end=" ")
    response = chat.process_input("Hello Kor'tana")
    assert response, "Empty response"
    print("✅")
    print(f"   Response: {response[:50]}...")
    
    # Test 5: Test memory
    print("5. Testing memory...", end=" ")
    chat.remember("user123", "Jim", "developer")
    memory = chat.memory.get_memory("user123")
    assert memory, "Memory not stored"
    print("✅")
    print(f"   Stored: {memory}")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED - KOR'TANA WORKS!")
    print("="*50)
    
except Exception as e:
    print(f"❌ FAILED")
    print(f"\nError: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
