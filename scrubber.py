import shutil
import time
import uuid
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fitz
from sanitizer_utils import scan_text

# Configuration - D: Drive Storage Volume
WATCH_DIR = Path(r"D:\Cyber_Physical_DBs\Research_Downloads")
CLEAN_DIR = Path(r"D:\Cyber_Physical_DBs\sources")
QUARANTINE_DIR = Path(r"D:\Cyber_Physical_DBs\Quarantine")

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

# V-07: Restricted allowlist
ALLOWED_EXTENSIONS = {'.pdf'}

executor = ProcessPoolExecutor(max_workers=4)

def setup_directories():
    for directory in [WATCH_DIR, CLEAN_DIR, QUARANTINE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def safe_move(src_path, dest_dir, prefix=""):
    src_path = Path(src_path)
    dest_dir = Path(dest_dir)
    try:
        suffix = uuid.uuid4().hex[:8]
        new_name = f"{prefix}{src_path.stem}_{suffix}{src_path.suffix}"
        dest_path = dest_dir / new_name
        shutil.move(str(src_path), str(dest_path))
        return True
    except Exception as e:
        print(f"Move failed: {e}")
        return False

def extract_text(filepath):
    path = Path(filepath)
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        return None
    ext = path.suffix.lower()
    if ext == '.pdf':
        try:
            with fitz.open(path) as doc:
                text = "".join(page.get_text() for page in doc)
                return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None
    return None # V-07: Non-PDFs return None to trigger quarantine

def scan_file(filepath):
    raw_content = extract_text(filepath)
    if raw_content is None:
        return False, "unsupported_format_or_corrupted"

    return scan_text(raw_content)

def wait_for_file_stable(filepath, timeout=30, interval=0.5):
    """V-06: Poll for file size stability before processing."""
    path = Path(filepath)
    last_size = -1
    elapsed = 0
    while elapsed < timeout:
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            return False
        if current_size == last_size and current_size > 0:
            try:
                path.rename(path)
                return True
            except PermissionError:
                pass
        last_size = current_size
        time.sleep(interval)
        elapsed += interval
    return False

def process_file(file_path):
    try:
        path = Path(file_path)
        filename = path.name
        if filename.startswith('.') or filename.endswith('.crdownload') or filename.endswith('.tmp'):
            return

        # V-07: Immediate extension check
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"[!] Blocking non-PDF file: {filename}")
            safe_move(path, QUARANTINE_DIR)
            return

        # V-06: Wait for download/write to finish
        if not wait_for_file_stable(path):
            print(f"[!] File timeout/instability: {filename}")
            return

        is_safe, trigger = scan_file(path)

        if is_safe:
            print(f"[✔] Clean: {filename}")
            safe_move(path, CLEAN_DIR)
        else:
            print(f"[!] QUARANTINE: {filename} (Trigger: {trigger})")
            safe_move(path, QUARANTINE_DIR)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

class DownloadHandler(FileSystemEventHandler):
    def _handle(self, event):
        if not event.is_directory:
            path = getattr(event, 'dest_path', event.src_path)
            executor.submit(process_file, path)

    on_created = on_moved = _handle

def process_existing_files():
    for child in WATCH_DIR.iterdir():
        if child.is_file():
            executor.submit(process_file, child)

if __name__ == "__main__":
    setup_directories()
    process_existing_files()
    print(f"[*] Scrubber ACTIVE. Watching {WATCH_DIR}...")
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        executor.shutdown(wait=True)
    observer.join()
