#!/usr/bin/env python3
"""
Example script demonstrating AutoGen adapter usage with Kor'tana.

This script shows how to interact with Kor'tana's AutoGen-compatible
endpoints for both simple chat and multi-agent collaboration.

Usage:
    python examples/autogen_example.py
    
Prerequisites:
    - Kor'tana server running at http://localhost:8000
    - Start server with: python -m uvicorn src.kortana.main:app --reload
"""

import asyncio

import httpx


async def example_simple_chat():
    """Example: Simple chat with AutoGen adapter."""
    print("=" * 60)
    print("Example 1: Simple Chat with AutoGen Adapter")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        request = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Can you explain what AutoGen is?"
                }
            ],
            "conversation_id": "example-chat-1"
        }
        
        print("\nSending request...")
        print(f"User: {request['messages'][0]['content']}")
        
        response = await client.post(
            "http://localhost:8000/adapters/autogen/chat",
            json=request,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nStatus: {data['status']}")
            print(f"Conversation ID: {data['conversation_id']}")
            
            if data.get("agent_responses"):
                agent_response = data["agent_responses"][0]
                print(f"\nAgent: {agent_response.get('agent')}")
                print(f"Response: {agent_response.get('content')[:200]}...")
        else:
            print(f"Error: {response.status_code}")


async def example_agent_status():
    """Example: Get agent status."""
    print("\n" + "=" * 60)
    print("Example 2: Agent Status Check")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/adapters/autogen/status",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFramework: {data['framework']}")
            print(f"Status: {data['status']}")
            print(f"Available Agents: {', '.join(data['available_agents'])}")
        else:
            print(f"Error: {response.status_code}")


async def main():
    """Run all examples."""
    print("\nAutoGen Adapter Examples for Kor'tana")
    print("=" * 60)
    
    try:
        await example_simple_chat()
        await example_agent_status()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("\nERROR: Could not connect to Kor'tana server")
        print("Start server: python -m uvicorn src.kortana.main:app --reload")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
