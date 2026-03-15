#!/usr/bin/env python
"""
Demo script showing Kor'tana's multilingual chat capabilities.

This script demonstrates:
1. Getting supported languages
2. Switching between languages
3. Detecting language from text
4. Making multilingual queries

Run this after starting the Kor'tana server:
    python -m uvicorn src.kortana.main:app --reload
"""

import httpx


BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


async def demo_supported_languages():
    """Demo: Get list of supported languages."""
    print_section("1. Supported Languages")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/language/supported")
        languages = response.json()
        
        print(f"Kor'tana supports {len(languages)} languages:")
        for code, name in languages.items():
            print(f"  {code:4s} - {name}")


async def demo_language_detection():
    """Demo: Detect language from text samples."""
    print_section("2. Language Detection")
    
    print("\nNote: Detection only works for non-Latin scripts.")
    print("Latin-script languages (EN/ES/FR/DE/PT/IT) are detected as English.\n")
    
    test_texts = [
        ("Hello, how are you?", "en", "English"),
        ("Bonjour, comment allez-vous?", "en", "English (Latin script limitation)"),
        ("Hola, ¿cómo estás?", "en", "English (Latin script limitation)"),
        ("你好，你好吗？", "zh", "Chinese"),
        ("こんにちは", "ja", "Japanese"),
    ]
    
    async with httpx.AsyncClient() as client:
        for text, expected_code, expected_desc in test_texts:
            response = await client.get(
                f"{BASE_URL}/language/detect",
                params={"text": text}
            )
            result = response.json()
            match = "✓" if result['detected_language'] == expected_code else "✗"
            print(f"  {match} '{text[:30]}'")
            print(f"    → Detected: {result['language_name']} ({result['detected_language']}) - Expected: {expected_desc}")


async def demo_language_switching():
    """Demo: Switch conversation language."""
    print_section("3. Language Switching")
    
    languages_to_try = [
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("en", "English"),
    ]
    
    async with httpx.AsyncClient() as client:
        for code, name in languages_to_try:
            response = await client.post(
                f"{BASE_URL}/language/switch",
                json={"language": code}
            )
            result = response.json()
            
            if result["success"]:
                print(f"  ✓ Switched to {name} ({code})")
            else:
                print(f"  ✗ Failed to switch to {name}")


async def demo_multilingual_queries():
    """Demo: Make queries in different languages."""
    print_section("4. Multilingual Queries (Core Endpoint)")
    
    queries = [
        ("en", "What is artificial intelligence?"),
        ("es", "¿Qué es la inteligencia artificial?"),
        ("fr", "Qu'est-ce que l'intelligence artificielle?"),
    ]
    
    print("\nNote: This demo shows the API structure.")
    print("Actual LLM responses require proper database and API key setup.\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for lang_code, query in queries:
            try:
                print(f"  Query in {lang_code}: '{query}'")
                response = await client.post(
                    f"{BASE_URL}/core/query",
                    json={"query": query, "language": lang_code}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✓ Response received (language: {result.get('language', 'N/A')})")
                else:
                    print(f"    ⚠ Status: {response.status_code}")
                    
            except Exception as e:
                print(f"    ⚠ Error: {type(e).__name__}")


async def demo_health_check():
    """Demo: Check multilingual support status."""
    print_section("5. Health Check")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        health = response.json()
        
        print(f"  Service: {health['service']}")
        print(f"  Status: {health['status']}")
        print(f"  Multilingual Support: {health.get('multilingual_support', False)}")
        print(f"  Supported Languages: {', '.join(health.get('supported_languages', []))}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  Kor'tana Multilingual Chat Framework Demo")
    print("=" * 60)
    print("\nMake sure the Kor'tana server is running:")
    print("  python -m uvicorn src.kortana.main:app --reload")
    
    try:
        await demo_health_check()
        await demo_supported_languages()
        await demo_language_detection()
        await demo_language_switching()
        await demo_multilingual_queries()
        
        print("\n" + "=" * 60)
        print("  Demo Complete!")
        print("=" * 60)
        print("\nFor more information, see: docs/MULTILINGUAL_SUPPORT.md\n")
        
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to Kor'tana server.")
        print("Please start the server first:")
        print("  python -m uvicorn src.kortana.main:app --reload\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
