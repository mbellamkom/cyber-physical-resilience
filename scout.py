import os
import time
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from scholarly import scholarly
from ddgs import DDGS
import requests
from discord_webhook import DiscordWebhook
from google import genai
from googlesearch import search as google_search

# Load environment variables
load_dotenv()

# Setup paths and environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
LOGS_DIR = RESEARCH_PATH / "logs"
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_FILE = LOGS_DIR / "seen_sources.txt"
REJECTED_LOG = LOGS_DIR / "rejected_sources.md"
TRIAGE_LOG = LOGS_DIR / "triage_log.md"

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RULES_PATH = Path(os.getenv("AGENT_RULES_PATH", RESEARCH_PATH / ".agent" / "rules" / "PROJECT_RULES.md"))

# Ensure files exist
if not REJECTED_LOG.exists():
    with open(REJECTED_LOG, "w", encoding="utf-8") as f:
        f.write("# Rejected Sources Log\n*These documents were scored as LOW relevance by the Cloud Agent (Gemini).* \n\n")

if not TRIAGE_LOG.exists():
    with open(TRIAGE_LOG, "w", encoding="utf-8") as f:
        f.write("# Triage Log\n*These documents were scoped out by the Local Bouncer (DeepSeek).* \n\n")

# Initialize Gemini Client for the Scout Agent
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_rules():
    """Load the project rules for the LLM context."""
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Evaluate this document for relevance."

def is_new_discovery(link, refresh_days=30):
    """Checks memory file to avoid alerting on seen links."""
    if not MEMORY_FILE.exists(): return True
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        if link in line:
            return False
    return True

def log_discovery(title, link, relevance, rationale):
    """Records a new discovery in the memory file."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"| [{title}]({link}) | {today} | {relevance} | {rationale} |\n")

def notify_detailed(title, link, score, rationale):
    """Sends scored alert to Discord."""
    status_icon = "🟢" if score == "HIGH" else "🟡"
    if is_new_discovery(link):
        message = f"🔍 **Scout Alert:** [{status_icon} {score}]\n**Title:** {title}\n**Link:** <{link}>\n\n**Agent Justification:** {rationale}"
        if WEBHOOK_URL: DiscordWebhook(url=WEBHOOK_URL, content=message).execute()
        log_discovery(title, link, score, rationale)

def log_rejection(title, link, rationale):
    """Logs low-quality hits to a local markdown file before marking them as seen."""
    if is_new_discovery(link):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(REJECTED_LOG, "a", encoding="utf-8") as f:
            f.write(f"- **[{today}]** [{title}]({link})\n  - *Rationale:* {rationale}\n\n")
        log_discovery(title, link, "LOW", rationale)

def log_triage_rejection(title, link, score, rationale):
    """Logs local Bouncer rejections to triage_log.md."""
    if is_new_discovery(link):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(TRIAGE_LOG, "a", encoding="utf-8") as f:
            f.write(f"- **[{today}]** [{score}] [{title}]({link})\n  - *Rationale:* {rationale}\n\n")
        log_discovery(title, link, score, rationale)

# --- STAGE 1: PYTHON SIEVE ---
SIEVE_KEYWORDS = [
    "safety", "security", "ics", "ot", "scada", "cyber-physical",
    "breach", "emergency", "override", "risk", "resilience", "hazard", 
    "industrial", "infrastructure"
]

def python_sieve(title, snippet):
    """Fast lexical zero-cost filter."""
    text = (title + " " + snippet).lower()
    return any(kw in text for kw in SIEVE_KEYWORDS)

# --- STAGE 2: LOCAL BOUNCER (OLLAMA) ---
def evaluate_with_ollama(snippets_bulk):
    """Sends a batch of snippets to local DeepSeek."""
    prompt = f"""
You are an expert triage assistant. Your goal is to evaluate these search snippets and identify the nexus between cybersecurity and physical safety/OT. If a document focuses solely on IT-standard data security while ignoring physical impact, score it LOW.
If it explicitly mentions major frameworks (NIST, ISO) but is completely silent on physical safety/OT-nexus, score it SILENT_ANOMALY.

SNIPPETS:
{json.dumps([{"index": i, "title": s["title"], "snippet": s["snippet"]} for i, s in enumerate(snippets_bulk)], indent=2)}

Evaluate each snippet. Output exactly a JSON array of objects with this format:
[
  {{"index": 0, "relevance": "HIGH" or "MEDIUM" or "LOW" or "SILENT_ANOMALY", "rationale": "One concise sentence."}}
]
"""
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "deepseek-r1:8b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=120)
        
        if response.status_code == 200:
            return json.loads(response.json()["response"])
    except Exception as e:
        print(f"[!] Local Bouncer offline or failed: {e}")
    return None

def process_final_score(item, rel, rat):
    """Handles the final routing for scoring."""
    title, link = item["title"], item["link"]
    print(f"  -> [Final] Score: {rel}")
    if rel == "IGNORE":
        print(f"  -> Skipping log for non-English source: {title[:40]}")
        return
        
    if rel in ["HIGH", "MEDIUM"]:
        notify_detailed(title, link, rel, rat)
    else:
        log_rejection(title, link, rat)

def process_batch(batch, rules_text):
    """Processes a batch of snippets through Stage 2 (Ollama) and Stage 3 (Gemini)."""
    if not batch: return
    print(f"[*] Processing batch of {len(batch)} snippets through Local Bouncer...")
    
    ollama_results = evaluate_with_ollama(batch)
    
    if ollama_results is None:
        print("[!] Falling back to Gemini individual evaluation (Throttled)...")
        for item in batch:
            rel_data = evaluate_snippet(item["title"], item["snippet"], rules_text)
            process_final_score(item, rel_data.get("relevance", "LOW"), rel_data.get("rationale", "No rationale."))
            time.sleep(10) # Fallback 10s wait logic
        return

    try:
        if isinstance(ollama_results, list):
            for res in ollama_results:
                idx = res.get("index")
                rel = res.get("relevance", "LOW")
                rat = res.get("rationale", "No rationale.")
                
                if idx is None or not isinstance(idx, int) or idx >= len(batch): continue
                
                item = batch[idx]
                title, link, snippet = item["title"], item["link"], item["snippet"]
                
                print(f"  -> [Ollama Triage] {title[:40]}... Score: {rel}")
                
                if rel in ["LOW", "SILENT_ANOMALY"]:
                    log_triage_rejection(title, link, rel, rat)
                else:
                    # STAGE 3: GEMINI
                    print(f"  -> [Gemini Confirming] {title[:40]}...")
                    gem_data = evaluate_snippet(title, snippet, rules_text)
                    process_final_score(item, gem_data.get("relevance", "LOW"), gem_data.get("rationale", "No rationale."))
                    time.sleep(10) # Optional spacing so Gemini doesn't burst if batch hits multiple HIGHs
    except Exception as e:
        print(f"[!] Error parsing batch results: {e}")

# --- GENAI CAPABILITIES ---
def generate_queries(topics):
    """Uses Gemini to brainstorm highly optimized search strings for both Scholar and general search engines."""
    print("[+] Agent is brainstorming query variants...")
    prompt = f"""
    You are an expert research librarian. The user is researching the following topics: {topics}.
    Generate exactly 3 highly optimized boolean search queries tailored for Google Scholar (focused on peer-reviewed rigorous data).
    Generate exactly 3 general web search queries (using search operators like `site:gov`, `site:iso.org`, or targeted natural language) to discover "Grey Literature" whitepapers. Do not use `filetype:pdf` as it triggers anti-bot protections.
    
    Output strictly as valid JSON:
    {{
        "scholar_queries": ["query1", "query2", "query3"],
        "ddg_queries": ["query4", "query5", "query6"]
    }}
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw)
        return data.get("scholar_queries", []), data.get("ddg_queries", [])
    except Exception as e:
        print(f"[!] Failed to generate or parse Agent queries: {e}")
        return topics, topics

def evaluate_snippet(title, snippet, rules_text):
    """Uses Gemini to read the search snippet and strictly score it against the Project Rules."""
    prompt = f"""
    You are an AI Librarian strictly enforcing the project rules.
    Evaluate the following search result title and abstract snippet for relevance to our research parameters.
    
    PROJECT RULES:
    {rules_text}
    
    ADDITIONAL RULE:
    The user only wants English sources. If the title or snippet is primarily in a language other than English, immediately score it as LOW relevance with the rationale "Non-English source."
    
    SEARCH SNIPPET:
    Title: {title}
    Snippet: {snippet}
    
    Evaluate strictly. Read the "Scout Agent Scoring Criteria" section from the Project Rules above. 
    Does this snippet meet the HIGH, MEDIUM, LOW, or IGNORE definition?
    Output strictly as valid JSON:
    {{
        "relevance": "HIGH" or "MEDIUM" or "LOW" or "IGNORE",
        "rationale": "One concise sentence explaining why it passed or failed based on the rules."
    }}
    """
    try:
        # 10s wait logic is now before the call in process_batch to avoid global delays
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception as e:
        return {"relevance": "LOW", "rationale": f"Gemini API or Parse error: {e}"}

# --- SEARCH ENGINES ---

def search_scholar(query, rules_text, limit=3):
    """Scrapes Google Scholar for academic papers."""
    print(f"\n[*] Scholar Search: {query}")
    batch = []
    try:
        search = scholarly.search_pubs(query)
        for _ in range(limit):
            paper = next(search)
            title = paper['bib'].get('title', 'Unknown')
            abstract = paper['bib'].get('abstract', '')
            link = paper.get('pub_url', 'No link')
            
            if link == 'No link' or not is_new_discovery(link): continue
            if not python_sieve(title, abstract):
                print(f"  -> System Sieve rejected: {title[:40]}...")
                continue
                
            batch.append({"title": title, "snippet": abstract, "link": link})
            time.sleep(5)
    except StopIteration:
        pass
    except Exception as e: print(f"[!] Scholar Error: {e}")
    process_batch(batch, rules_text)

def search_ddg(query, rules_text, limit=4):
    """Scrapes DuckDuckGo for Grey Literature & government sources."""
    print(f"\n[*] Web Search (DDG): {query}")
    batch = []
    try:
        from ddgs import ddgs
        with ddgs() as duck:
            results = duck.text(query, max_results=limit)
            for res in results:
                title = res.get('title', 'Unknown')
                snippet = res.get('body', '')
                link = res.get('href', 'No link')
                
                if link == 'No link' or not is_new_discovery(link): continue
                if not python_sieve(title, snippet):
                    print(f"  -> System Sieve rejected: {title[:40]}...")
                    continue
                    
                batch.append({"title": title, "snippet": snippet, "link": link})
                time.sleep(2)
    except Exception as e:
        print(f"[!] DDG Error: {e}")
    process_batch(batch, rules_text)

def search_google(query, rules_text, limit=4):
    """Scrapes Google Search for Grey Literature as a DDG fallback."""
    print(f"\n[*] Web Search (Google): {query}")
    batch = []
    try:
        results = google_search(query, num_results=limit, advanced=False)
        for res in results:
            if isinstance(res, str):
                title = "Google Result"
                snippet = "Snippet unavailable for basic search."
                link = res
            else:
                title = str(getattr(res, 'title', 'Unknown'))
                snippet = str(getattr(res, 'description', ''))
                link = str(getattr(res, 'url', 'No link'))
            
            if link == 'No link' or not is_new_discovery(link): continue
            if not python_sieve(title, snippet):
                print(f"  -> System Sieve rejected: {title[:40]}...")
                continue
                
            batch.append({"title": title, "snippet": snippet, "link": link})
            time.sleep(2)
    except Exception as e:
        print(f"[!] Google Search Error: {e}")
    process_batch(batch, rules_text)

if __name__ == "__main__":
    rules = load_rules()
    topics_env = os.getenv("RESEARCH_TOPICS", "NIST 800-82 safety over security, FEMA Lifelines Cyber Dependency")
    topics_list = [t.strip() for t in topics_env.split(",") if t.strip()]
    
    # AI Generation Phase
    scholar_queries, ddg_queries = generate_queries(topics_list)
    
    print("[=] Executing Pluggable Hybrid Search...")
    
    # Academic Pass
    for sq in scholar_queries:
        search_scholar(sq, rules)
        
    # Grey Literature Pass
    for dq in ddg_queries:
        search_ddg(dq, rules)
        search_google(dq, rules)