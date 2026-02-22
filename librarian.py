# --- This script runs the AI Auditor on all PDFs in the /sources directory ---

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Load environment variables (like API keys and paths) from the .env file
load_dotenv()

# Setup paths from environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH"))
SOURCE_DIR = Path(os.getenv("SOURCE_DIR"))
AUDIT_DIR = RESEARCH_PATH / "audits"

# Initialize the Gemini GenAI Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_audit():
    # Define paths to the agent's rules and skills
    rules_path = RESEARCH_PATH / ".agent" / "rules" / "PROJECT_RULES.md"
    skills_path = RESEARCH_PATH / ".agent" / "skills" / "auditor.md"
    
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
        
        # Write the report to a new markdown file in the audits directory
        with open(report_file, "w", encoding="utf-8") as f: f.write(response.text)
        
        print(f"[✔] Audit Complete.")
        
        # Sleep for 12 seconds to avoid hitting API rate limits
        time.sleep(12)

if __name__ == "__main__":
    run_audit()