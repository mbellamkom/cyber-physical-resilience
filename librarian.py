# --- This script runs the AI Auditor on all PDFs in the /sources directory ---

import os
import time
import shutil
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import uuid
from qdrant_client import QdrantClient, models

# Load environment variables (like API keys and paths) from the .env file
load_dotenv()

# Setup paths from environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH", "."))
SOURCE_DIR = Path(os.getenv("SOURCE_DIR", "sources"))
AUDIT_DIR = RESEARCH_PATH / "audits"
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "archive"))

# Initialize the Gemini GenAI Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Qdrant Client
qdrant_path = os.getenv("QDRANT_LOCAL_PATH", ".qdrant_db")
qdrant = QdrantClient(path=qdrant_path)
COLLECTION_NAME = "global_resilience_vault"

# Ensure collection exists
try:
    qdrant.get_collection(COLLECTION_NAME)
except Exception:
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
    )

def run_audit():
    # Define paths to the agent's rules and skills, allowing override via .env
    rules_path = Path(os.getenv("AGENT_RULES_PATH", RESEARCH_PATH / ".agent" / "rules" / "PROJECT_RULES.md"))
    skills_path = Path(os.getenv("AGENT_SKILLS_PATH", RESEARCH_PATH / ".agent" / "skills" / "auditor.md"))
    
    # Read the rules and skills into memory
    with open(rules_path, "r", encoding="utf-8") as f: rules = f.read()
    with open(skills_path, "r", encoding="utf-8") as f: skill = f.read()

    # Find all PDFs in the source directory
    files = list(SOURCE_DIR.glob("*.pdf"))
    if not files:
        print("[!] No PDFs found in /sources. Download some from Discord first!")
        return

    # Loop through each PDF and audit it if it hasn't been audited yet
    for pdf in files:
        report_file = AUDIT_DIR / f"{pdf.stem}_audit.md"
        # Skip this file if an audit report already exists
        if report_file.exists(): continue

        print(f"[+] Auditing: {pdf.name}...")
        
        # Upload the PDF to the Gemini File API
        up_file = client.files.upload(file=pdf)
        
        # Construct the prompt with the rules, skills, and instructions
        prompt = f"RULES:\n{rules}\nSKILL:\n{skill}\nTASK: Generate AUDIT_REPORT.md"
        
        # Generate the audit report using the Gemini 2.5 Flash model
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[up_file, prompt])
        report_text = response.text
        
        # Write the report to a new markdown file in the audits directory
        with open(report_file, "w", encoding="utf-8") as f: f.write(report_text)
        
        # --- Qdrant Insertion Logic ---
        print(f"[+] Embedding report for {pdf.name} into Qdrant...")
        # Create a simple chunking strategy (e.g., split by double newline)
        chunks = [c.strip() for c in report_text.split("\n\n") if len(c.strip()) > 50]
        
        if chunks:
            # Embed chunks using Gemini's text-embedding-004 model
            embed_response = client.models.embed_content(
                model="text-embedding-004", 
                contents=chunks
            )
            
            points = []
            for i, embedding in enumerate(embed_response.embeddings):
                points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.values,
                    payload={
                        "filename": pdf.name,
                        "chunk_index": i,
                        "text": chunks[i]
                    }
                ))
            
            qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"[✔] Embedded {len(chunks)} chunks.")
            
        print(f"[✔] Audit Complete.")
        
        # Archive the processed PDF
        shutil.move(str(pdf), str(ARCHIVE_DIR / pdf.name))
        print(f"[+] Moved {pdf.name} to archive.")
        
        # Sleep for 12 seconds to avoid hitting API rate limits
        time.sleep(12)

if __name__ == "__main__":
    run_audit()