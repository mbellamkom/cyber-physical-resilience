import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH"))
SOURCE_DIR = Path(os.getenv("SOURCE_DIR"))
AUDIT_DIR = RESEARCH_PATH / "audits"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_audit():
    rules_path = RESEARCH_PATH / ".agent" / "rules" / "PROJECT_RULES.md"
    skills_path = RESEARCH_PATH / ".agent" / "skills" / "auditor.md"
    
    with open(rules_path, "r", encoding="utf-8") as f: rules = f.read()
    with open(skills_path, "r", encoding="utf-8") as f: skill = f.read()

    files = list(SOURCE_DIR.glob("*.pdf"))
    if not files:
        print("[!] No PDFs found in /sources. Download some from Discord first!")
        return

    for pdf in files:
        report_file = AUDIT_DIR / f"{pdf.stem}_audit.md"
        if report_file.exists(): continue

        print(f"[+] Auditing: {pdf.name}...")
        up_file = client.files.upload(file=pdf)
        prompt = f"RULES:\n{rules}\nSKILL:\n{skill}\nTASK: Generate AUDIT_REPORT.md"
        
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[up_file, prompt])
        with open(report_file, "w", encoding="utf-8") as f: f.write(response.text)
        print(f"[✔] Audit Complete.")
        time.sleep(12)

if __name__ == "__main__":
    run_audit()