import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

def run_diagnostics():
    """Runs a series of checks to ensure the environment is ready for the Librarian Agent."""
    print("Initializing Cyber-Physical Resilience Diagnostics...\n")
    
    # 1. Load the .env file containing API keys and configuration paths
    if load_dotenv():
        print("[OK] .env file loaded successfully.")
    else:
        print("[ERROR] Could not find or read the .env file.")
        return

    # 2. Check the standard set of directories the system relies on
    print("\n--- Checking File Paths ---")
    paths_to_check = {
        "Source Directory": os.getenv("SOURCE_DIR"),
        "Archive Directory": os.getenv("ARCHIVE_DIR"),
        "Audit Directory": os.path.join(os.getenv("RESEARCH_PATH", "."), "audits"),
        "Database Directory": os.getenv("QDRANT_LOCAL_PATH")
    }

    # Verify each path, creating missing directories dynamically if needed
    for name, path in paths_to_check.items():
        if path and os.path.exists(path):
            print(f"[OK] {name} is accessible at: {path}")
        elif path:
            print(f"[WARNING] {name} path doesn't exist yet. Creating it...")
            os.makedirs(path, exist_ok=True)
            print(f"     -> Created: {path}")
        else:
            print(f"[ERROR] {name} is completely missing from the .env file.")

    # 3. Test the Vector Database (Qdrant) to ensure memory modules will function
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