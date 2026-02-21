import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

def run_diagnostics():
    print("Initializing Cyber-Physical Resilience Diagnostics...\n")
    
    # 1. Load the .env file
    if load_dotenv():
        print("[OK] .env file loaded successfully.")
    else:
        print("[ERROR] Could not find or read the .env file.")
        return

    # 2. Check the Directories
    print("\n--- Checking File Paths ---")
    paths_to_check = {
        "Source Directory": os.getenv("SOURCE_DIR"),
        "Archive Directory": os.getenv("ARCHIVE_DIR"),
        "Database Directory": os.getenv("QDRANT_LOCAL_PATH")
    }

    for name, path in paths_to_check.items():
        if path and os.path.exists(path):
            print(f"[OK] {name} is accessible at: {path}")
        elif path:
            print(f"[WARNING] {name} path doesn't exist yet. Creating it...")
            os.makedirs(path, exist_ok=True)
            print(f"     -> Created: {path}")
        else:
            print(f"[ERROR] {name} is completely missing from the .env file.")

    # 3. Test the Vector Database (Qdrant)
    print("\n--- Testing Database Engine (Qdrant Local) ---")
    try:
        db_path = os.getenv("QDRANT_LOCAL_PATH")
        # Initialize Qdrant in local disk-persistence mode
        client = QdrantClient(path=db_path)
        print(f"[OK] Qdrant Engine is active and locked to: {db_path}")
        print("\nAll systems nominal. Ready for Librarian Agent.")
    except Exception as e:
        print(f"[ERROR] Database failed to spin up: {e}")

if __name__ == "__main__":
    run_diagnostics()