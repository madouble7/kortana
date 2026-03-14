#!/usr/bin/env python3
"""
Kor'tana Voice Chat Interface
Real-time voice interaction with the autonomous system
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import speech_recognition as sr
except ImportError:
    print("Installing speech_recognition...")
    os.system(f"{sys.executable} -m pip install speech_recognition -q")
    import speech_recognition as sr

try:
    import pyttsx3
except ImportError:
    print("Installing pyttsx3...")
    os.system(f"{sys.executable} -m pip install pyttsx3 -q")
    import pyttsx3

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests


class VoiceChatInterface:
    """Voice interface for Kor'tana communication"""

    def __init__(self, api_url="http://localhost:8000/api/always-on"):
        self.api_url = api_url
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)  # Adjust speech rate
        self.running = True
        self.conversation_log = []

    def speak(self, text):
        """Convert text to speech and play it"""
        print(f"\n🤖 Kor'tana: {text}\n")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Speech synthesis error: {e}")

    def listen(self):
        """Listen for user voice input"""
        print("\n🎤 Listening... (speak now)")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10)

            text = self.recognizer.recognize_google(audio)
            print(f"👤 You: {text}")
            return text.lower().strip()

        except sr.UnknownValueError:
            error_msg = "I didn't catch that. Could you repeat?"
            self.speak(error_msg)
            return None
        except sr.RequestError as e:
            error_msg = f"Voice service error: {str(e)}"
            self.speak(error_msg)
            return None
        except Exception as e:
            error_msg = f"Listening error: {str(e)}"
            self.speak(error_msg)
            return None

    def api_call(self, endpoint, method="GET", data=None):
        """Make REST API call to Kor'tana"""
        try:
            url = f"{self.api_url}/{endpoint}"
            headers = {"Content-Type": "application/json"}

            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=5)

            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def process_voice_command(self, text):
        """Process voice commands and interact with Kor'tana"""
        if not text:
            return

        # Command keywords
        if any(
            word in text for word in ["status", "how are you", "what's up", "what are you doing"]
        ):
            result = self.api_call("status")
            if "error" not in result:
                running = result.get("running", False)
                tasks = result.get("tasks_total", 0)
                response = f"I'm {'actively monitoring and executing tasks' if running else 'currently paused'}. "
                response += f"I have {tasks} tasks in my queue."
                self.speak(response)
            else:
                self.speak("I'm having trouble connecting. Let me try again.")

        elif any(word in text for word in ["start", "begin", "activate", "wake up"]):
            result = self.api_call("start", method="POST")
            if "error" not in result:
                self.speak("Autonomous monitoring activated. I'm now actively working on tasks.")
            else:
                self.speak("Failed to start monitoring.")

        elif any(word in text for word in ["stop", "pause", "sleep", "rest"]):
            result = self.api_call("stop", method="POST")
            if "error" not in result:
                self.speak("Monitoring paused. I'm standing by.")
            else:
                self.speak("Failed to stop monitoring.")

        elif any(
            word in text
            for word in [
                "tasks",
                "what are you working on",
                "show me tasks",
                "list tasks",
            ]
        ):
            result = self.api_call("tasks?limit=5")
            if "error" not in result and result.get("tasks"):
                tasks = result["tasks"][:3]
                response = f"I have {len(tasks)} recent tasks. "
                for i, task in enumerate(tasks, 1):
                    task_name = task.get("title", "Unknown task")
                    response += f"Task {i}: {task_name}. "
                self.speak(response)
            else:
                self.speak("No active tasks at the moment.")

        elif any(
            word in text for word in ["dashboard", "overview", "summary", "tell me everything"]
        ):
            result = self.api_call("dashboard")
            if "error" not in result:
                stats = result.get("stats", {})
                response = "Here's my status: "
                response += f"Total tasks: {stats.get('tasks_total', 0)}. "
                response += f"Completed: {stats.get('tasks_completed', 0)}. "
                response += f"Failed: {stats.get('tasks_failed', 0)}. "
                response += f"Human interventions needed: {stats.get('human_interventions', 0)}."
                self.speak(response)
            else:
                self.speak("I can't access my dashboard right now.")

        elif any(word in text for word in ["check", "force check", "scan", "look now"]):
            result = self.api_call("force-check", method="POST")
            if "error" not in result:
                self.speak("Running immediate check. Scanning for new tasks.")
            else:
                self.speak("Check failed.")

        elif any(word in text for word in ["health", "are you okay", "system check"]):
            result = self.api_call("health")
            if "error" not in result:
                status = result.get("status", "unknown")
                response = f"System health: {status}."
                self.speak(response)
            else:
                self.speak("Health check failed.")

        elif any(word in text for word in ["metrics", "performance", "stats", "how am i doing"]):
            result = self.api_call("metrics")
            if "error" not in result:
                metrics = result.get("metrics", {})
                response = "Performance metrics: "
                response += f"Uptime: {metrics.get('uptime_hours', 0)} hours. "
                response += f"Tasks per hour: {metrics.get('task_rate', 0)}."
                self.speak(response)
            else:
                self.speak("I can't retrieve my metrics.")

        elif any(word in text for word in ["help", "commands", "what can you do", "options"]):
            help_text = """I can help you with: asking my status, starting or stopping monitoring,
            viewing my tasks, showing my dashboard, forcing a check, checking system health,
            viewing performance metrics, and more. What would you like to know?"""
            self.speak(help_text)

        elif any(word in text for word in ["approve", "yes", "proceed", "go ahead"]):
            self.speak("What task would you like to approve? Please give me the task ID.")
            task_id = self.listen()
            if task_id:
                result = self.api_call(
                    f"tasks/{task_id}/approve",
                    method="POST",
                    data={"approved": True, "notes": ""},
                )
                if "error" not in result:
                    self.speak(f"Task {task_id} approved. Proceeding with execution.")
                else:
                    self.speak("Approval failed.")

        elif any(word in text for word in ["retry", "again", "try again"]):
            self.speak("Which task should I retry? Please give me the task ID.")
            task_id = self.listen()
            if task_id:
                result = self.api_call(f"tasks/{task_id}/retry", method="POST")
                if "error" not in result:
                    self.speak(f"Task {task_id} is being retried.")
                else:
                    self.speak("Retry failed.")

        elif any(word in text for word in ["exit", "quit", "goodbye", "bye", "stop talking"]):
            self.speak("Goodbye! I'll be here if you need me.")
            self.running = False

        elif any(word in text for word in ["hello", "hi", "hey", "greetings"]):
            self.speak(
                "Hello! I'm Kor'tana, your autonomous development assistant. How can I help you?"
            )

        else:
            # Default response for unrecognized commands
            self.speak(
                f"I'm not sure about '{text}'. Try asking me about my status, tasks, or to start monitoring."
            )

        # Log conversation
        self.conversation_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "user": text,
                "response": "Voice response played",
            }
        )

    def save_conversation(self):
        """Save conversation log to file"""
        log_file = Path("voice_chat_log.json")
        try:
            with open(log_file, "w") as f:
                json.dump(self.conversation_log, f, indent=2)
            print(f"\n✅ Conversation saved to {log_file}")
        except Exception as e:
            print(f"Error saving conversation: {e}")

    def run(self):
        """Main voice chat loop"""
        print("\n" + "=" * 60)
        print("🤖  KOR'TANA VOICE CHAT")
        print("=" * 60)
        print("\n🎤 Voice chat started. Say 'help' for commands, 'exit' to quit.\n")

        # Welcome message
        self.speak("Voice chat activated. I'm ready to listen. What can I help you with?")

        try:
            while self.running:
                try:
                    # Listen for command
                    user_input = self.listen()

                    if user_input:
                        # Process the voice command
                        self.process_voice_command(user_input)

                    # Small delay before next listen
                    time.sleep(0.5)

                except KeyboardInterrupt:
                    self.speak("Voice chat ended.")
                    self.running = False
                except Exception as e:
                    print(f"Error in voice loop: {e}")
                    self.speak(f"An error occurred: {str(e)}")

        finally:
            self.save_conversation()
            print("\n✅ Voice chat session ended.")


def main():
    """Entry point"""
    print("\n📱 Checking dependencies...")

    # Try to initialize the interface
    try:
        voice_chat = VoiceChatInterface()
        print("✅ Dependencies ready!")
        print("⚠️  Make sure your microphone is connected and working.")
        input("Press Enter to start voice chat with Kor'tana...")

        voice_chat.run()

    except Exception as e:
        print(f"\n❌ Error initializing voice chat: {e}")
        print("\nMake sure:")
        print("  1. Kor'tana server is running on http://localhost:8000")
        print("  2. Your microphone is connected")
        print("  3. Audio permissions are granted")
        sys.exit(1)


if __name__ == "__main__":
    import time

    main()
