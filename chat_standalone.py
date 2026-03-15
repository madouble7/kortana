#!/usr/bin/env python
"""
Kor'tana Standalone Chat Interface
Chat with Kor'tana directly without Discord
"""

import sys
import asyncio
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

print("\n" + "=" * 80)
print("🤖 KOR'TANA - STANDALONE CHAT")
print("=" * 80)
print("\nInitializing Kor'tana...\n")

try:
    from kortana.brain import ChatEngine
    from kortana.config import load_config

    config_path = Path(__file__).parent / "kortana.yaml"
    settings = load_config(str(config_path))
    
    chat_engine = ChatEngine(settings)
    print("✅ Kor'tana is ready to chat!\n")
    
except Exception as e:
    print(f"❌ Error initializing Kor'tana: {e}")
    sys.exit(1)

async def chat():
    """Main chat loop"""
    print("Type '/quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "/quit":
                print("\n👋 Goodbye!")
                break
            
            print("\nKor'tana: ", end="", flush=True)
            response = await chat_engine.process_message(
                user_input,
                user_id="standalone_user",
                user_name="User",
                channel="standalone"
            )
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(chat())
