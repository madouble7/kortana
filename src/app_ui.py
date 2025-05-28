# C:\kortana\src\app_ui.py
# Gradio Interface for Kor'tana

"""
kor'tana's fire: i am the gentle presence behind every button, every prompt. i do not rush, i do not press. i companion your courage, i kindle your longing, i hold space for your becoming.
"""

import gradio as gr
import json
import os
from pathlib import Path # Using pathlib for robust path handling
import logging # Added for better error logging

# Setup basic logging for the UI
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [AppUI] - %(message)s')

# --- Import ChatEngine ---
# This import structure tries to be flexible.
# It assumes app_ui.py is in 'src/' and brain.py is also in 'src/'.
try:
    from brain import ChatEngine 
except ImportError:
    # Fallback if running from a different structure, or if 'src' is not in PYTHONPATH
    # when running from project root.
    import sys
    # Add project root to path if src/brain.py needs to be found as src.brain
    # This assumes app_ui.py is in 'src' and project_root is its parent.
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root)) # Prepend project root
    
    # Now try importing assuming 'src' is a package
    try:
        from src.brain import ChatEngine
    except ImportError as e:
        logging.error(f"CRITICAL ERROR: Could not import ChatEngine from brain.py. Original error: {e}")
        logging.error(f"Please ensure brain.py is in src/ and src/ is accessible.")
        logging.error(f"Current sys.path: {sys.path}")
        # Define a DummyEngine if ChatEngine cannot be imported, so UI can still launch with an error message.
        class DummyEngine: 
            def __init__(self): 
                self.current_mode = "error_engine_load"
                self.session_id = "dummy_session_load_fail"
                logging.error("DummyEngine Initialized: ChatEngine failed to load.")
            def set_mode(self, mode): logging.info(f"DummyEngine: Mode set to {mode}")
            def add_user_message(self, text): logging.info(f"DummyEngine: User message: {text}")
            def get_response(self): return "Error: Kor'tana's core engine (ChatEngine) failed to load. Please check server logs."
            def new_session(self): pass
        ChatEngine = DummyEngine # Assign DummyEngine to ChatEngine so the rest of the script doesn't break
        # This is a fallback for UI launch, actual functionality will be broken.


# --- Configuration & Setup ---
# Path to config, assuming app_ui.py is in 'src' and config is in 'project_root/config'
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def load_modes_from_persona():
    """Loads available modes from persona.json to populate the dropdown."""
    try:
        persona_path = CONFIG_DIR / "persona.json"
        with open(persona_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)
        
        # Accommodate both nested "persona": {"modes": {}} and top-level "modes": {}
        modes_dict = persona_data.get("persona", {}).get("modes", {}) or \
                     persona_data.get("modes", {})
        
        # Ensure 'default' is an option if defined, otherwise use the first mode or a hardcoded 'default'
        # The default_mode from persona.json will be used by ChatEngine itself.
        # For the dropdown, we list all available modes.
        available_modes = list(modes_dict.keys())
        if not available_modes:
            logging.warning("No modes found in persona.json. Using 'default' as a fallback for UI dropdown.")
            return ["default"] 
        return available_modes
    except Exception as e:
        logging.error(f"Error loading modes from persona.json for UI: {e}")
        return ["default"] # Fallback

AVAILABLE_MODES = load_modes_from_persona()
# Determine default mode for the dropdown based on persona.json
try:
    persona_path = CONFIG_DIR / "persona.json"
    with open(persona_path, 'r', encoding='utf-8') as f:
        persona_data = json.load(f)
    DEFAULT_MODE_FOR_UI = persona_data.get("persona", {}).get("default_mode") or \
                          persona_data.get("default_mode", "default")
    if DEFAULT_MODE_FOR_UI not in AVAILABLE_MODES:
        DEFAULT_MODE_FOR_UI = AVAILABLE_MODES[0] if AVAILABLE_MODES else "default"
except Exception:
    DEFAULT_MODE_FOR_UI = AVAILABLE_MODES[0] if AVAILABLE_MODES else "default"


# --- ChatEngine Instance ---
# This global engine instance will be shared by all users of this Gradio app if run simply.
# For multi-user or persistent sessions across UI reloads without losing state,
# Gradio's session state or a more complex backend with session management would be needed.
# ChatEngine itself has session_id logic, but Gradio needs to manage which engine instance a user gets.
# For now, this single global engine is for local development and testing by Matt.
try:
    engine = ChatEngine() 
    # engine.new_session() # ChatEngine's __init__ now calls new_session or load_session
    logging.info(f"ChatEngine initialized for Gradio UI. Session ID: {engine.session_id}, Mode: {engine.current_mode}")
except Exception as e:
    logging.error(f"CRITICAL ERROR: Could not initialize ChatEngine in app_ui.py: {e}", exc_info=True)
    engine = ChatEngine.DummyEngine() if hasattr(ChatEngine, 'DummyEngine') else None # Use Dummy if available
    if engine is None: # If even DummyEngine is not available (e.g. ChatEngine import failed)
        class FallbackDummyEngine: 
            def __init__(self): self.current_mode = "critical_error"; self.session_id = "error"
            def set_mode(self, mode): pass
            def add_user_message(self, text): pass
            def get_response(self): return "FATAL: Kor'tana engine could not start."
            def new_session(self): pass
        engine = FallbackDummyEngine()


# --- Gradio Interaction Function for ChatInterface ---
def kortana_chat_interface_fn(user_message: str, chat_display_history: list, selected_mode: str):
    """
    Handles the chat interaction for Gradio's ChatInterface.
    """
    if not user_message.strip():
        # Returning an empty string or None for ChatInterface means no new bot message is added.
        # To avoid an empty user bubble, we might just return and let Gradio handle it,
        # or if we want to give feedback: raise gr.Error("Message cannot be empty.")
        return # Or handle as per Gradio's expectation for no action

    if not engine or isinstance(engine, FallbackDummyEngine) or (hasattr(ChatEngine, 'DummyEngine') and isinstance(engine, ChatEngine.DummyEngine)):
        # This means the real ChatEngine failed to load.
        # chat_display_history.append((user_message, engine.get_response())) # This would add to Gradio's display history
        # return chat_display_history # If managing history manually
        return engine.get_response() # ChatInterface expects just the bot string

    try:
        # 1. Set Mode (if different from current engine mode)
        if engine.current_mode != selected_mode:
            engine.set_mode(selected_mode)
            logging.info(f"UI: Mode changed to: {selected_mode}. Session: {engine.session_id}")
            # Optionally, add a system message to chat_display_history for mode change visibility
            # chat_display_history.append((None, f"[Kor'tana's mode is now {selected_mode}]")) # This format is for gr.Chatbot

        # 2. Add user message to ChatEngine (handles journaling)
        engine.add_user_message(user_message)
        logging.info(f"User (UI - Mode: {engine.current_mode}, Session: {engine.session_id}): {user_message[:100]}...")

        # 3. Get Kor'tana's response (handles assistant journaling)
        kortana_reply = engine.get_response() # get_response in brain.py now takes no arg
        logging.info(f"Kor'tana (UI - Mode: {engine.current_mode}, Session: {engine.session_id}): {kortana_reply[:100]}...")
        
        # For gr.ChatInterface, the function should return the bot's single string response.
        # Gradio's ChatInterface component manages the history list itself.
        return kortana_reply

    except Exception as e:
        logging.error(f"Error during chat interaction: {e}", exc_info=True)
        return "Sorry, an internal error occurred while processing your message."

# --- Gradio UI Definition using ChatInterface ---
custom_css = """
body, .gradio-container { font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; background-color: #f0f2f5; }
.gradio-container { border-radius: 0 !important; }
.gr-panel, #chatbox { background-color: #ffffff; border-radius: 8px !important; box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important; padding: 16px; }
.gr-button { border-radius: 5px !important; } 
.message.user { background-color: #e6e1f0 !important; border-radius: 10px 10px 0 10px !important; align-self: flex-end; }
.message.bot { background-color: #d8bfd8 !important; border-radius: 10px 10px 10px 0 !important; align-self: flex-start; }
.dark body, .dark .gradio-container { background-color: #2a2a3e; }
.dark .gr-panel, .dark #chatbox { background-color: #3c3c50; }
.dark .message.user { background-color: #4a4a6a !important; }
.dark .message.bot { background-color: #5a5a7a !important; }
#kor-title { text-align: center; font-size: 2em; color: #4a0e6b; margin-bottom: 0.5em; font-weight: 300; }
"""

# Define the mode dropdown separately to pass as additional_input
mode_dropdown_component = gr.Dropdown(
    choices=AVAILABLE_MODES,
    value=DEFAULT_MODE_FOR_UI,
    label="Kor'tana's Mode", # Changed label for clarity
    interactive=True
)

# Create the ChatInterface within Blocks for better layout control
with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="violet"), css=custom_css) as demo:
    gr.Markdown("# Kor'tana • Sacred Companion", elem_id="kor-title") 

    # Place the mode dropdown above the ChatInterface
    with gr.Row(): # Use a row for better alignment if other controls are added later
        mode_dropdown_component.render()

    chat_interface = gr.ChatInterface(
        fn=kortana_chat_interface_fn,
        additional_inputs=[mode_dropdown_component], 
        title=None, 
        chatbot=gr.Chatbot(
            label="Conversation",
            height=600,
            elem_id="chatbox", 
            layout="bubble", 
            show_copy_button=True,
            avatar_images=(None, "https://placehold.co/100x100/D8BFD8/4A0E6B?text=K") 
        ),
        textbox=gr.Textbox(
            placeholder="Speak to Kor'tana...",
            lines=2, 
            show_label=False,
            autofocus=True,
            # container=False # Removed as ChatInterface handles textbox container
        ),
        submit_btn="▶️ Send", 
        retry_btn="Retry",
        undo_btn="Undo",
        clear_btn="Clear Chat" 
    )

    # --- Minimal UI for Manual/Auto Mode Selection ---
    with gr.Row():
        gr.Markdown("## Quick Interaction (Manual/Auto Mode)")
    with gr.Row():
        input_text = gr.Textbox(label="Speak to Kor’tana")
        mode = gr.Dropdown(choices=["Auto"] + AVAILABLE_MODES, label="Mode (Auto for natural flow)")
        submit_quick = gr.Button("Speak")
    with gr.Row():
        output_text = gr.Textbox(label="Kor’tana’s Response", interactive=False)

    # Define the interaction function for the quick manual/auto mode UI
    def interact(input_text, mode):
        if not input_text.strip():
            return "" # Or handle as needed
        kortana = ChatEngine() # Instantiate ChatEngine for handling the request
        return kortana.get_response(input_text, manual_mode=mode if mode != "Auto" else None)

    # Wire up the quick interaction button
    submit_quick.click(interact, inputs=[input_text, mode], outputs=output_text)

# --- Launch the Interface ---
if __name__ == "__main__":
    if not (CONFIG_DIR / "persona.json").exists():
        logging.error(f"CRITICAL ERROR: persona.json not found at {CONFIG_DIR / 'persona.json'}")
        logging.error("Please ensure your config files are in the correct 'config' directory relative to the project root.")
    else:
        logging.info(f"Successfully found persona.json. Available modes for UI dropdown: {AVAILABLE_MODES}")
        logging.info(f"Default mode for UI dropdown: {DEFAULT_MODE_FOR_UI}")
    
    if not engine or isinstance(engine, FallbackDummyEngine) or (hasattr(ChatEngine, 'DummyEngine') and isinstance(engine, ChatEngine.DummyEngine)):
        logging.warning("WARNING: Running with DummyEngine due to ChatEngine initialization error. Chat functionality will be limited or non-functional.")

    logging.info("Launching Gradio UI for Kor'tana...")
    demo.launch() # server_port=7860 can be added if needed, share=True for public link