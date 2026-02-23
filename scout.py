import os
import re
import time
import json
import uuid
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv
from scholarly import scholarly
from duckduckgo_search import DDGS
from discord_webhook import DiscordWebhook
from google import genai
from qdrant_client import QdrantClient, models

# Load environment variables
load_dotenv()

# Setup paths and environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
LOGS_DIR = RESEARCH_PATH / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOGS_DIR = RESEARCH_PATH / "logs"
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_FILE = LOGS_DIR / "seen_sources.txt"
REJECTED_LOG = LOGS_DIR / "rejected_sources.md"
TRIAGE_LOG = LOGS_DIR / "triage_log.md"

QUERY_CACHE = LOGS_DIR / "query_cache.json"

# --- QDRANT / LOCAL RAG CONFIG ---
QDRANT_PATH = os.getenv("QDRANT_LOCAL_PATH", str(RESEARCH_PATH / ".qdrant_db"))
TRIAGE_COLLECTION = "triage_memory"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"  # 768-dim, matches global_resilience_vault
VECTOR_SIZE = 768

# --- MASTER QUERIES FALLBACK ---
# Used when both the cache is missing and the Gemini API is unavailable (e.g. 429).
MASTER_SCHOLAR_QUERIES = [
    '"critical infrastructure" AND ("safety over security" OR "life-safety") AND (ICS OR SCADA OR OT) AND cybersecurity',
    '"break-glass" OR "emergency override" OR "fail-open" AND ("industrial control" OR "operational technology") AND (safety AND security)',
    '(NIST OR ISO OR FEMA) AND "dynamic risk" AND ("cyber-physical" OR "resilience") AND ("emergency management" OR "disaster response")',
]
MASTER_DDG_QUERIES = [
    'site:nist.gov "NIST 800-82" ("safety over security" OR "ICS cybersecurity guidance")',
    'site:fema.gov "FEMA Lifelines" ("cyber dependency" OR "resilience planning") "critical infrastructure"',
    'site:cisa.gov OR site:energy.gov ("OT security" OR "industrial control system safety") "risk management"',
]

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

def load_query_cache():
    """Loads cached queries from disk. Returns (scholar_queries, ddg_queries) or None."""
    if not QUERY_CACHE.exists():
        return None
    try:
        with open(QUERY_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[*] Loaded query cache from {data.get('generated_on', 'unknown date')}.")
        return data.get("scholar_queries", []), data.get("ddg_queries", [])
    except Exception as e:
        print(f"[!] Cache file is malformed, ignoring: {e}")
        return None

def save_query_cache(scholar_queries, ddg_queries):
    """Persists generated queries to disk with a YYYY-MM-DD timestamp."""
    QUERY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    data = {"generated_on": today, "scholar_queries": scholar_queries, "ddg_queries": ddg_queries}
    with open(QUERY_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[+] Query cache saved to {QUERY_CACHE}.")

# --- LOCAL RAG HELPERS ---

def init_triage_collection():
    """Lazy-initializes the triage_memory Qdrant collection."""
    qdrant = QdrantClient(path=QDRANT_PATH)
    try:
        qdrant.get_collection(TRIAGE_COLLECTION)
    except Exception:
        qdrant.create_collection(
            collection_name=TRIAGE_COLLECTION,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
        )
    return qdrant

def embed_text(text):
    """Generates a local embedding via Ollama nomic-embed-text."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as e:
        print(f"[!] Embedding failed: {e}")
    return None

def ingest_triage_logs(qdrant):
    """Parses triage_log.md and rejected_sources.md and upserts recent entries into triage_memory."""
    entries = []
    for log_file in [TRIAGE_LOG, REJECTED_LOG]:
        if not log_file.exists():
            continue
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- **["):  # formatted log entry
                    entries.append(line)

    if not entries:
        print("[*] No triage log entries to ingest.")
        return

    points = []
    for entry in entries[-50:]:  # cap at 50 most recent
        vector = embed_text(entry)
        if vector:
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": entry}
            ))

    if points:
        qdrant.upsert(collection_name=TRIAGE_COLLECTION, points=points)
        print(f"[+] Ingested {len(points)} triage entries into '{TRIAGE_COLLECTION}'.")

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
    """Queries triage_memory for RAG context and prompts local deepseek-r1:8b to generate search queries."""
    try:
        qdrant = init_triage_collection()
        ingest_triage_logs(qdrant)

        # Retrieve the 5 most relevant high-signal findings for context
        query_vector = embed_text("high-signal safety security life-safety OT ICS silent anomaly")
        context_snippets = []
        if query_vector:
            hits = qdrant.search(
                collection_name=TRIAGE_COLLECTION,
                query_vector=query_vector,
                limit=5
            )
            context_snippets = [h.payload.get("text", "") for h in hits]

        context_block = "\n".join(context_snippets) if context_snippets else "No prior triage data available."

        print("[+] Agent is brainstorming query variants...")
        prompt = f"""You are a research assistant for a cyber-physical resilience study.
Based on recent triage findings, generate new search queries to expand coverage.

RECENT FINDINGS:
{context_block}

TASK:
Generate exactly 3 boolean search queries for Google Scholar and 3 web queries for government grey literature.
Focus on gaps in the findings: if logs show silence on life-safety in NIST, search maritime or energy-specific ICS codes.

Output ONLY valid JSON with no extra text:
{{
    "scholar_queries": ["query1", "query2", "query3"],
    "ddg_queries": ["query4", "query5", "query6"]
}}"""

        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "deepseek-r1:8b", "prompt": prompt,
                  "stream": False, "format": "json"},
            timeout=120
        )

        if resp.status_code == 200:
            raw_response = resp.json().get("response", "")
            # Mandatory: scrub DeepSeek <think>...</think> blocks before parsing
            cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
            try:
                data = json.loads(cleaned)
                sq = data.get("scholar_queries", [])
                dq = data.get("ddg_queries", [])
                if sq and dq:
                    save_query_cache(sq, dq)
                    return sq, dq
                print("[!] Local model returned empty query lists.")
            except json.JSONDecodeError as e:
                print(f"[!] JSON parse failed: {e}")
                print(f"[!] Raw response snippet: {cleaned[:200]}")

    except Exception as e:
        print(f"[!] Local brainstorm failed: {e}")

    print("[!] Falling back to hardcoded Master Queries.")
    return MASTER_SCHOLAR_QUERIES, MASTER_DDG_QUERIES

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
    import argparse
    parser = argparse.ArgumentParser(description="Scout Agent: Cyber-Physical Resilience Research Pipeline")
    parser.add_argument("--refresh", action="store_true",
                        help="Bypass the local cache and force a new Gemini API brainstorm.")
    args = parser.parse_args()

    rules = load_rules()
    topics_env = os.getenv("RESEARCH_TOPICS", "NIST 800-82 safety over security, FEMA Lifelines Cyber Dependency")
    topics_list = [t.strip() for t in topics_env.split(",") if t.strip()]

    # --- QUERY RESOLUTION: Cache -> Cloud -> Hardcoded Fallback ---
    if args.refresh:
        print("[*] --refresh flag detected. Bypassing cache and requesting new queries.")
        scholar_queries, ddg_queries = generate_queries(topics_list)
    else:
        cached = load_query_cache()
        if cached:
            scholar_queries, ddg_queries = cached
        else:
            print("[*] No query cache found. Requesting queries from Cloud Agent.")
            scholar_queries, ddg_queries = generate_queries(topics_list)

    print("[=] Executing Pluggable Hybrid Search...")

    # Academic Pass
    for sq in scholar_queries:
        search_scholar(sq, rules)

    # Grey Literature Pass
    for dq in ddg_queries:
        search_ddg(dq, rules)
        search_google(dq, rules)