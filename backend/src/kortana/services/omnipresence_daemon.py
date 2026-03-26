import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class CodeSteeringHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_modified = {}

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.py'):
            return

        current_time = time.time()
        if current_time - self.last_modified.get(event.src_path, 0) < 2:
            return

        self.last_modified[event.src_path] = current_time

        try:
            with open(event.src_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if '# KOR\\'TANA:' in content or '# KORTANA:' in content:
                print(f\"\n[KOR'TANA OMNIPRESENCE] Steering command detected in {event.src_path}\")
                print(\"[KOR'TANA] Analyzing diff... Preparing proactive sync.\")
                # Here we would hook into the actual Gemini engine and patch the file
        except Exception as e:
            pass

def run_watcher():
    path = os.path.join(os.getcwd(), 'backend', 'src')
    print(f\"[KOR'TANA OMNIPRESENCE] Watcher initialized. Monitoring: {path}\")
    print(\"[KOR'TANA] Waiting for steering comments (e.g. # KORTANA: fix this function)\")

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

if __name__ == \"__main__\":
    run_watcher()
