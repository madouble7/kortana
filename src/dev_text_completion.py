import os
from llm_clients.openai_client import OpenAIClient
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model_name = "gpt-4.1-nano-2025-04-14"

if not api_key:
    print("Error: OPENAI_API_KEY not set in environment or .env file.")
    exit(1)

client = OpenAIClient(api_key=api_key, model_name=model_name)

system_prompt = "You are Kor'tana, a helpful, creative, and soulful assistant."

print("Kor'tana Dev Playground\n=========================")
print("1. Text prompt only\n2. Text + Image (image URL)")
mode = input("Choose mode (1 or 2): ").strip()

if mode == "2":
    user_prompt = input("Enter your text prompt: ").strip()
    if not user_prompt:
        user_prompt = "what teams are playing in this image?"
    image_url = input("Enter image URL: ").strip()
    if not image_url:
        image_url = "https://upload.wikimedia.org/wikipedia/commons/3/3b/LeBron_James_Layup_%28Cleveland_vs_Brooklyn_2018%29.jpg"
    messages = [
        {"role": "user", "content": user_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }
    ]
else:
    user_prompt = input("Enter a prompt (or leave blank for a unicorn bedtime story): ").strip()
    if not user_prompt:
        user_prompt = "write a one-sentence bedtime story about a unicorn."
    messages = [
        {"role": "user", "content": user_prompt}
    ]

response = client.generate_response(
    system_prompt=system_prompt,
    messages=messages
)

print("\nKor'tana says:")
print(response["content"]) 