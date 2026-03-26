import time
import os
import threading
import sys
from typing import Set, Dict, Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = os.path.join(os.getcwd(), "backend")
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

processing_files: Set[str] = set()

def process_file_with_kortana(file_path: str, content: str) -> None:
    try:
        from src.kortana.services.gemini import gemini_service
        gemini = gemini_service
        print(f"[KOR'TANA] Processing steering command in {os.path.basename(file_path)}...")

        prompt = f"""You are KOR'TANA, an omnipresent autonomous AI.
You are watching this file: {os.path.basename(file_path)}

The user has embedded a steering comment starting with "# KOR'TANA:" or "# KORTANA:".
Find that comment, follow its instructions, remove the steering comment, and output the ENTIRE updated file content.

CRITICAL: ONLY OUTPUT THE RAW CODE. DO NOT WRAP IN MARKDOWN.
Start exactly at the first line of code.

CURRENT FILE CONTENT:
{content}"""

        updated_content = gemini.analyze_text_sync(prompt)
        
        if isinstance(updated_content, str) and "Error during analysis:" in updated_content:
            print(f"[KOR'TANA] Model API Error: {updated_content}")
            return

        if isinstance(updated_content, str) and updated_content.startswith("`python"):
            updated_content = updated_content[9:]
        elif isinstance(updated_content, str) and updated_content.startswith("`"):
            updated_content = updated_content[3:]
        if isinstance(updated_content, str) and updated_content.endswith("`"):
            updated_content = updated_content[:-3]

        if isinstance(updated_content, str):
            updated_content = updated_content.strip() + "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"[KOR'TANA] {os.path.basename(file_path)} updated successfully and implicitly saved.")

    except Exception as e:
        print(f"[KOR'TANA] Omnipresence processing failed: {e}")
    finally:
        processing_files.discard(file_path)

class CodeSteeringHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.last_modified: Dict[str, float] = {}

    def on_modified(self, event: Any) -> None:
        if event.is_directory or not str(event.src_path).endswith(".py"):
            return

        if event.src_path in processing_files:
            return

        current_time = time.time()
        if current_time - self.last_modified.get(event.src_path, 0) < 2:
            return

        self.last_modified[event.src_path] = current_time

        try:
            with open(event.src_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "# KOR'TANA:" in content or "# KORTANA:" in content:
                print(f"[KOR'TANA OMNIPRESENCE] Steering command detected in {event.src_path}")
                processing_files.add(event.src_path)
                threading.Thread(
                    target=process_file_with_kortana,
                    args=(event.src_path, content)
                ).start()

        except Exception as e:
            pass

def run_watcher() -> None:
    path = os.path.join(os.getcwd(), "backend", "src")
    print(f"[KOR'TANA OMNIPRESENCE] Watcher initialized. Monitoring: {path}")
    print("[KOR'TANA] Core attached. I am watching every keystroke and save. Waiting for steering commands...")

    event_handler = CodeSteeringHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_watcher()
