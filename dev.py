import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_app()

    def start_app(self):
        if self.process:
            self.process.terminate()
        print("\n[Dev] Change detected! Restarting ScholarTrack...")
        # Path to your venv python if needed, otherwise just "python"
        self.process = subprocess.Popen(["python", "main.py"])

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.start_app()

if __name__ == "__main__":
    # You might need to run: pip install watchdog
    try:
        from watchdog.observers import Observer
    except ImportError:
        print("Installing watcher tool...")
        subprocess.run(["pip", "install", "watchdog"])

    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()
    print("[Dev] Hot Reload Active. Editing any .py file will restart the app.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
