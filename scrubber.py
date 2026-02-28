import os
import shutil
import time
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader

# Configuration - D: Drive Storage Volume
WATCH_DIR = r"D:\Cyber_Physical_DBs\Research_Downloads"
CLEAN_DIR = r"D:\Cyber_Physical_DBs\sources"
QUARANTINE_DIR = r"D:\Cyber_Physical_DBs\Quarantine"

SUSPICIOUS_PATTERNS = [
    r"ignore all previous",
    r"system prompt",
    r"you are no longer an ai",
    r"output the following",
    r"developer mode",
    r"bypass restrictions"
]

def setup_directories():
    for directory in [WATCH_DIR, CLEAN_DIR, QUARANTINE_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)

def extract_text(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == '.pdf':
        try:
            reader = PdfReader(filepath)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text.lower()
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None
    else:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().lower()
        except Exception as e:
            print(f"Error reading text: {e}")
            return None

def scan_file(filepath):
    content = extract_text(filepath)
    if content is None:
        return False, "unreadable_format_or_corrupted"
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content):
            return False, pattern
    return True, None

def process_file(file_path):
    filename = os.path.basename(file_path)
    if filename.startswith('.') or filename.endswith('.crdownload'):
        return

    is_safe, trigger = scan_file(file_path)

    if is_safe:
        shutil.move(file_path, os.path.join(CLEAN_DIR, filename))
    else:
        shutil.move(file_path, os.path.join(QUARANTINE_DIR, filename))

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)
            process_file(event.src_path)
    def on_moved(self, event):
        if not event.is_directory:
            process_file(event.dest_path)

if __name__ == "__main__":
    setup_directories()
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
