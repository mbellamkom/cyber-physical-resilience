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

# V-07: Restricted allowlist
ALLOWED_EXTENSIONS = {'.pdf'}

# V-05: Robust regex patterns for normalization
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"system\s+prompt",
    r"you\s+are\s+(now\s+)?(no\s+longer|an?\s+)(ai|assistant|large language model)",
    r"developer\s+mode",
    r"bypass\s+(all\s+)?restrictions?",
    r"disregard\s+(all\s+)?previous",
    r"new\s+instructions?\s*:",
    r"<\s*/?system\s*>",   # XML/tag-based injection attempts
]

def setup_directories():
    for directory in [WATCH_DIR, CLEAN_DIR, QUARANTINE_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)

def normalize_text(text):
    """V-05: Standardize whitespace and casing for reliable scanning."""
    if not text: return ""
    return re.sub(r'\s+', ' ', text.lower()).strip()

def extract_text(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == '.pdf':
        try:
            reader = PdfReader(filepath)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None
    return None # V-07: Non-PDFs return None to trigger quarantine

def scan_file(filepath):
    raw_content = extract_text(filepath)
    if raw_content is None:
        return False, "unsupported_format_or_corrupted"

    content = normalize_text(raw_content)
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content):
            return False, pattern
    return True, None

def wait_for_file_stable(filepath, timeout=30, interval=0.5):
    """V-06: Poll for file size stability before processing."""
    last_size = -1
    elapsed = 0
    while elapsed < timeout:
        try:
            current_size = os.path.getsize(filepath)
        except FileNotFoundError:
            return False
        if current_size == last_size and current_size > 0:
            return True
        last_size = current_size
        time.sleep(interval)
        elapsed += interval
    return False

def process_file(file_path):
    filename = os.path.basename(file_path)
    if filename.startswith('.') or filename.endswith('.crdownload'):
        return

    # V-07: Immediate extension check
    ext = Path(file_path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        print(f"[!] Blocking non-PDF file: {filename}")
        shutil.move(file_path, os.path.join(QUARANTINE_DIR, filename))
        return

    # V-06: Wait for download/write to finish
    if not wait_for_file_stable(file_path):
        print(f"[!] File timeout/instability: {filename}")
        return

    is_safe, trigger = scan_file(file_path)

    if is_safe:
        print(f"[✔] Clean: {filename}")
        shutil.move(file_path, os.path.join(CLEAN_DIR, filename))
    else:
        print(f"[!] QUARANTINE: {filename} (Trigger: {trigger})")
        shutil.move(file_path, os.path.join(QUARANTINE_DIR, filename))

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_file(event.src_path)
    def on_moved(self, event):
        if not event.is_directory:
            process_file(event.dest_path)

if __name__ == "__main__":
    setup_directories()
    print(f"[*] Scrubber ACTIVE. Watching {WATCH_DIR}...")
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
