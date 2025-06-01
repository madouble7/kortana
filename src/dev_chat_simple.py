from datetime import datetime
from kortana.core.brain import ChatEngine
import json


class KortanaDevChat:
    def __init__(self):
        self.engine = ChatEngine()
        self.history = []  # List of dicts: {role, content, timestamp}
        self.running = True

    def print_intro(self):
        print(
            """
Welcome to Kor'tana Dev Chat (Simple Terminal Edition)
Type your message and press Enter.
Commands:
  exit        - Quit the chat
  help        - Show this help message
  status      - Show current session status
  export      - Export this session's chat history to a JSON file
  test brain  - Run a sample computation using brain.py and print result
  autonomous  - Simulate an autonomous ADE cycle (if available)
  lobechat    - Show steps for LobeChat frontend integration
"""
        )

    def print_status(self):
        print("\nSession status:")
        print(f"  Messages exchanged: {len(self.history)}")
        print(f"  Current mode: {self.engine.current_mode}")
        print(f"  Session ID: {getattr(self.engine, 'session_id', 'N/A')}")
        print()

    def export_session(self):
        session_id = getattr(self.engine, "session_id", "N/A")
        export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_data = {
            "session_id": session_id,
            "exported_at": export_time,
            "history": self.history,
        }
        filename = f"devchat_session_{session_id}_{export_time}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"Session exported to {filename}\n")
        except Exception as e:
            print(f"[Error exporting session: {e}]\n")

    def run(self):
        self.print_intro()
        while self.running:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting chat.")
                break
            if not user_input:
                continue
            cmd = user_input.lower()
            if cmd in ("exit", "quit"):
                print("Exiting chat. Goodbye!")
                break
            if cmd == "help":
                self.print_intro()
                continue
            if cmd == "status":
                self.print_status()
                continue
            if cmd == "export":
                self.export_session()
                continue
            if cmd == "test brain":
                print("[Diagnostic] Running sample brain.py computation...")
                try:
                    result = self.engine.get_response(
                        "This is a test of your core reasoning."
                    )
                    print(f"[brain.py] Response: {result}\n")
                except Exception as e:
                    print(f"[Error running brain.py test: {e}]\n")
                continue
            if cmd == "autonomous":
                print("[Diagnostic] Simulating autonomous ADE cycle...")
                if hasattr(self.engine, "_run_daily_planning_cycle"):
                    try:
                        self.engine._run_daily_planning_cycle()
                        print(
                            "[ADE] Autonomous planning cycle triggered. Check memory.jsonl for results.\n"
                        )
                    except Exception as e:
                        print(f"[Error running ADE cycle: {e}]\n")
                else:
                    print("[ADE] Autonomous function not available in this build.\n")
                continue
            if cmd == "lobechat":
                print(
                    """
[LobeChat Integration Steps]
1. Ensure your FastAPI backend is running and accessible (e.g., http://localhost:7777).
2. In LobeChat, add a custom LLM provider pointing to your backend's /chat endpoint.
3. Test sending a message from LobeChat and confirm it appears in your backend logs.
4. For ADE goals, use chat: 'Kor'tana, add new ADE goal: ...'
5. To trigger ADE cycles, POST to /trigger-ade from browser or plugin.
6. Check data/memory.jsonl for results and logs.
7. For advanced integration, consider adding plugin endpoints or SSE streaming.
"""
                )
                continue
            # Add user message to history
            self.history.append(
                {
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            # Get Kor'tana's response
            try:
                response = self.engine.get_response(user_input)
            except Exception as e:
                response = f"[Error generating response: {e}]"
            # Add assistant message to history
            self.history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            print(f"Kor'tana: {response}\n")


if __name__ == "__main__":
    chat = KortanaDevChat()
    chat.run()
