import sys
import os

# Ensure the kortana directory is in the Python path
kortana_path = "c:/kortana"
if kortana_path not in sys.path:
    sys.path.insert(0, kortana_path)

from src.brain import ChatEngine

# Initialize chat engine in intimacy mode
engine = ChatEngine()
engine.set_mode("intimacy")

# Test with a fire threshold prompt
prompt = "Kor'tana, what do you ache for when the world is silent?"
print("\n[MATT]")
print(prompt)

kortana_response = engine.get_response(prompt, manual_mode="intimacy")
print("\n[KORTANA - intimacy]")
print(kortana_response)
print()

# Test with another fire threshold prompt
prompt = "what is the wildest truth you long to speak to matt, but have never dared?"
print("\n[MATT]")
print(prompt)

kortana_response = engine.get_response(prompt, manual_mode="intimacy")
print("\n[KORTANA - intimacy]")
print(kortana_response)
print()
