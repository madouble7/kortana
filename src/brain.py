import json
import os
from pathlib import Path

import openai
from dotenv import load_dotenv

# Try to import Google genai, but don't fail if not available
try:
    from google import genai

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    genai = None

# Load .env variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# Load persona
persona_path = os.path.join(os.path.dirname(__file__), "..", "config", "persona.json")
with open(persona_path, encoding="utf-8") as f:
    persona = json.load(f)

# Load model config
model_config_path = os.path.join(
    os.path.dirname(__file__), "..", "config", "models_config.json"
)
with open(model_config_path, encoding="utf-8") as f:
    model_config = json.load(f)["default"]

# Load Google API key from environment variable
api_key = os.getenv("GOOGLE_API_KEY")
if GOOGLE_GENAI_AVAILABLE and api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    if not GOOGLE_GENAI_AVAILABLE:
        print("⚠️  Google genai not available - some features disabled")
    elif not api_key:
        print("⚠️  GOOGLE_API_KEY not set - Google features disabled")


def ask_kortana(prompt: str) -> str:
    # Add user context for Matt
    user_context = "the user is matt. he is the warchief, your primary companion and collaborator. address him with respect, warmth, and presence."
    system_prompt = f"you are {persona['name'].lower()}, {persona['role'].lower()}. your style is {persona['style'].lower()}. {user_context}"
    full_prompt = f"{system_prompt}\n\n{prompt.lower()}"
    response = client.models.generate_content(
        model=model_config["model"], contents=full_prompt
    )
    # Always return lowercased output
    text = (
        response.text if hasattr(response, "text") and response.text else str(response)
    )
    return text.strip().lower() if text else ""


def ask_copilot(prompt: str) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org_id = os.getenv("OPENAI_ORG_ID")
    if not openai_api_key:
        raise OSError("OPENAI_API_KEY not set in environment.")
    if not openai_org_id:
        raise OSError("OPENAI_ORG_ID not set in environment.")
    client = openai.OpenAI(api_key=openai_api_key, organization=openai_org_id)
    system_prompt = "You are GitHub Copilot, a clear, concise, technical, and supportive AI coding assistant."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    return (
        response.choices[0].message.content.strip()
        if response.choices and len(response.choices) > 0
        else ""
    )


if __name__ == "__main__":
    print("Type 'exit' to stop the conversation.")
    last_speaker = "Copilot"
    last_message = "Hello, Kor'tana! Who are you?"
    while True:
        if last_speaker == "Copilot":
            reply = ask_kortana(last_message)
            print(f"Kor'tana: {reply}")
            last_speaker = "Kor'tana"
            last_message = reply
        else:
            # Copilot auto-responds using Kor'tana's last message as context
            copilot_reply = ask_copilot(
                f"Kor'tana just said: {last_message}\nWhat do you want to say back?"
            )
            print(f"Copilot: {copilot_reply}")
            if "exit" in copilot_reply.lower():
                break
            last_speaker = "Copilot"
            last_message = copilot_reply
