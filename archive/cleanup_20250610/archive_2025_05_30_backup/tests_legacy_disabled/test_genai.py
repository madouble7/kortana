"""Test script for Google GenAI client"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file in the current working directory
print("Loading environment variables from .env file...")
load_dotenv()

print("Attempting to import GoogleGenAIClient...")
try:
    # Import the Google GenAI client from your project structure
    from kortana.llm_clients.genai_client import GoogleGenAIClient
except ImportError as e:
    print(f"ERROR: Could not import GoogleGenAIClient: {e}")
    print(
        "Ensure src/llm_clients/genai_client.py and related factory/init files are correct."
    )
    sys.exit(1)

print("Successfully imported GoogleGenAIClient.")

# Retrieve and validate the API key
print("Checking for GOOGLE_API_KEY...")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env file or environment variables.")
    print(
        "Please ensure a .env file exists in the c:\\kortana directory with your GOOGLE_API_KEY."
    )
    sys.exit(1)
else:
    print("✓ Successfully loaded GOOGLE_API_KEY from environment.")

# Instantiate the client and make a simple API call
print("\nAttempting to initialize GoogleGenAIClient...")
try:  # Try initializing with API key parameter first - use widely available model
    client = GoogleGenAIClient(api_key=api_key, model_name="gemini-1.5-flash-latest")
    print("✓ GoogleGenAIClient initialized successfully.")

    # Test with a simple prompt
    system_prompt = "You are a helpful assistant."
    messages = [
        {
            "role": "user",
            "content": "Say 'Hello, this is a test response from Google GenAI!' in exactly those words.",
        }
    ]

    print("Sending test request to Google GenAI...")
    print(f"System prompt: {system_prompt}")
    print(f"User message: {messages[0]['content']}")

    # Call the generate_response method
    response = client.generate_response(system_prompt, messages)

    print("\n=== FULL API RESPONSE ===")
    print(response)
    print("=== END RESPONSE ===")

    # Try to extract the generated text based on expected response structure
    if isinstance(response, dict):
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"\n✓ Generated Text: {content}")
        elif "text" in response:
            print(f"\n✓ Generated Text: {response['text']}")
        else:
            print(
                "\n⚠ Could not extract specific text from response. Please inspect full response above."
            )
    else:
        print(f"\n⚠ Unexpected response type: {type(response)}")

    print("\n🎉 Basic test completed successfully!")

    # Test with custom generation parameters (to verify GenerationConfig handling)
    print("\n" + "=" * 50)
    print("TESTING CUSTOM GENERATION PARAMETERS")
    print("=" * 50)

    test_params = {"temperature": 0.7, "max_output_tokens": 150, "top_p": 0.9}

    print(f"Testing with parameters: {test_params}")

    # Test the generate_response method with custom parameters
    custom_response = client.generate_response(
        system_prompt="You are a creative assistant.",
        messages=[
            {
                "role": "user",
                "content": "Write a very short creative story about a robot.",
            }
        ],
        **test_params,
    )

    print("\n=== CUSTOM PARAMETERS RESPONSE ===")
    print(custom_response)
    print("=== END CUSTOM RESPONSE ===")

    if isinstance(custom_response, dict) and "choices" in custom_response:
        content = custom_response["choices"][0]["message"]["content"]
        print(f"\n✓ Custom Parameters Generated Text: {content}")

    print("\n🎉 All tests completed successfully!")

except Exception as e:
    print(f"\n❌ ERROR during Google GenAI API call: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
