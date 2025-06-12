#!/usr/bin/env python
"""
End-to-end test script for validating the LobeChat-Kor'tana integration.

This script simulates LobeChat requests to Kor'tana's LobeChat adapter API endpoint
to verify that the integration works correctly.

Usage:
    python scripts/test_lobe_integration.py
"""

import argparse
import json
import os
import sys
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def send_request(url, api_key, message, conversation_id=None):
    """Send a request to the LobeChat adapter API."""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    data = {"content": message, "conversation_id": conversation_id or str(uuid.uuid4())}

    req = Request(
        url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST"
    )

    try:
        response = urlopen(req)
        return json.loads(response.read().decode("utf-8")), response.getcode()
    except HTTPError as e:
        print(f"Error: {e.code} - {e.reason}")
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            print(f"Error details: {error_body}")
        except:
            print("Could not parse error response")
        return None, e.code


def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description="Test LobeChat-Kor'tana integration")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/lobe/chat",
        help="URL of the LobeChat adapter API endpoint",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("KORTANA_API_KEY"),
        help="API key for authentication (defaults to KORTANA_API_KEY env var)",
    )
    parser.add_argument(
        "--messages",
        type=int,
        default=3,
        help="Number of test messages to send (default: 3)",
    )
    args = parser.parse_args()

    if not args.api_key:
        print(
            "Error: API key not provided. Set KORTANA_API_KEY environment variable or use --api-key"
        )
        return 1

    print(f"Testing LobeChat integration with {args.url}")
    print("-" * 80)

    # Test basic messages
    test_messages = [
        "Hello, Kor'tana! How are you today?",
        "What can you tell me about your memory system?",
        "Do you remember our previous messages in this conversation?",
    ]

    # Use the same conversation ID for all messages to test conversation context
    conversation_id = str(uuid.uuid4())
    print(f"Using conversation ID: {conversation_id}")

    for i, message in enumerate(test_messages[: args.messages], 1):
        print(f"\nTest {i}: Sending message: '{message}'")

        start_time = time.time()
        response_data, status_code = send_request(
            args.url, args.api_key, message, conversation_id
        )
        end_time = time.time()

        if status_code == 200 and response_data:
            print(f"✅ Success (HTTP {status_code}, {(end_time - start_time):.2f}s)")
            print(f"Response ID: {response_data.get('id')}")
            print(f"Response content: {response_data.get('content')}")
        else:
            print(f"❌ Failed (HTTP {status_code})")

        # Add a short delay between requests
        time.sleep(1)

    print("\nAll tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
