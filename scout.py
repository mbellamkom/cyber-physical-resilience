import os
import time
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from scholarly import scholarly
from duckduckgo_search import DDGS
import requests
from discord_webhook import DiscordWebhook
from google import genai

# Load environment variables
load_dotenv()

# Setup paths and environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
MEMORY_FILE = RESEARCH_PATH / "seen_sources.txt"
REJECTED_LOG = RESEARCH_PATH / "rejected_sources.md"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RULES_PATH = Path(os.getenv("AGENT_RULES_PATH", RESEARCH_PATH / ".agent" / "rules" / "PROJECT_RULES.md"))

# Ensure files exist
if not REJECTED_LOG.exists():
    with open(REJECTED_LOG, "w", encoding="utf-8") as f:
        f.write("# Rejected Sources Log\n*These documents were scored as LOW relevance by the Scout Agent based on the current Project Rules.* \n\n")

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
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 2:
                seen_link, date_str = parts[0], parts[1]
                if seen_link == link:
                    try:
                        last_seen = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        if (datetime.datetime.now() - last_seen).days < refresh_days:
                            return False 
                    except ValueError: continue
    return True

def log_discovery(link, relevance="UNKNOWN", source_type="UNKNOWN", notes=""):
    """Records a new discovery in the memory file."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # Clean notes to not break our | delimiter or lines
    clean_notes = str(notes).replace('\n', ' ').replace('|', '-')
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{link}|{today}|{relevance}|{source_type}|{clean_notes}\n")

def notify_detailed(title, link, score, rationale, source_type="UNKNOWN"):
    """Sends scored alert to Discord."""
    status_icon = "🟢" if score == "HIGH" else "🟡"
    if is_new_discovery(link):
        message = f"🔍 **Scout Alert:** [{status_icon} {score}]\n**Title:** {title}\n**Link:** <{link}>\n\n**Agent Justification:** {rationale}"
        if WEBHOOK_URL: DiscordWebhook(url=WEBHOOK_URL, content=message).execute()
        log_discovery(link, score, source_type, rationale)

def log_rejection(title, link, rationale, source_type="UNKNOWN"):
    """Logs low-quality hits to a local markdown file before marking them as seen."""
    if is_new_discovery(link):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(REJECTED_LOG, "a", encoding="utf-8") as f:
            f.write(f"- **[{today}]** [{title}]({link})\n  - *Rationale:* {rationale}\n\n")
        log_discovery(link, "LOW", source_type, rationale)

# --- GENAI CAPABILITIES ---

def generate_queries(topics):
    """Uses Gemini to brainstorm highly optimized search strings for both Scholar and general search engines."""
    print("[+] Agent is brainstorming query variants...")
    prompt = f"""
    You are an expert research librarian. The user is researching the following topics: {topics}.
    Generate exactly 3 highly optimized boolean search queries tailored for Google Scholar (focused on peer-reviewed rigorous data).
    Generate exactly 3 general web search queries (using search operators like `site:gov`, `site:iso.org`, or targeted natural language for DuckDuckGo) to discover "Grey Literature" whitepapers.
    
    Output strictly as valid JSON:
    {{
        "scholar_queries": ["query1", "query2", "query3"],
        "ddg_queries": ["query4", "query5", "query6"]
    }}
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    try:
        # Strip markdown code blocks if present
        raw = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw)
        return data.get("scholar_queries", []), data.get("ddg_queries", [])
    except Exception as e:
        print(f"[!] Failed to parse Agent queries: {e}")
        return topics, topics

def evaluate_snippet(title, snippet, rules_text):
    """Uses Gemini to read the search snippet and strictly score it against the Project Rules."""
    prompt = f"""
    You are an AI Librarian strictly enforcing the project rules.
    Evaluate the following search result title and abstract snippet for relevance to our research parameters.
    
    PROJECT RULES:
    {rules_text}
    
    SEARCH SNIPPET:
    Title: {title}
    Snippet: {snippet}
    
    Evaluate strictly. Read the "Scout Agent Scoring Criteria" section from the Project Rules above. 
    Does this snippet meet the HIGH, MEDIUM, or LOW definition?
    Output strictly as valid JSON:
    {{
        "relevance": "HIGH" or "MEDIUM" or "LOW",
        "rationale": "One concise sentence explaining why it passed or failed based on the rules."
    }}
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    try:
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"relevance": "LOW", "rationale": "Parse error."}

# --- SEARCH ENGINES ---

def search_scholar(query, rules_text, limit=3):
    """Scrapes Google Scholar for academic papers."""
    print(f"\n[*] Scholar Search: {query}")
    try:
        search = scholarly.search_pubs(query)
        for _ in range(limit):
            paper = next(search)
            title = paper['bib'].get('title', 'Unknown')
            abstract = paper['bib'].get('abstract', '')
            link = paper.get('pub_url', 'No link')
            
            # Skip if we already saw it or if link is bad
            if link == 'No link' or not is_new_discovery(link): continue
            
            eval_data = evaluate_snippet(title, abstract, rules_text)
            rel = eval_data.get("relevance", "LOW")
            rat = eval_data.get("rationale", "No rationale.")
            
            print(f"  -> Analyzed {title[:40]}... Score: {rel}")
            if rel in ["HIGH", "MEDIUM"]:
                notify_detailed(title, link, rel, rat, source_type="Academic")
            else:
                log_rejection(title, link, rat, source_type="Academic")
                
            time.sleep(15) # Scholar rate limits
    except StopIteration:
        pass
    except Exception as e: print(f"[!] Scholar Error: {e}")

def search_ddg(query, rules_text, limit=4):
    """Scrapes DuckDuckGo for Grey Literature & government sources."""
    print(f"\n[*] Web Search (DDG): {query}")
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=limit)
            for res in results:
                title = res.get('title', 'Unknown')
                snippet = res.get('body', '')
                link = res.get('href', 'No link')
                
                if link == 'No link' or not is_new_discovery(link): continue
                
                eval_data = evaluate_snippet(title, snippet, rules_text)
                rel = eval_data.get("relevance", "LOW")
                rat = eval_data.get("rationale", "No rationale.")
                
                print(f"  -> Analyzed {title[:40]}... Score: {rel}")
                if rel in ["HIGH", "MEDIUM"]:
                    notify_detailed(title, link, rel, rat, source_type="Grey Literature")
                else:
                    log_rejection(title, link, rat, source_type="Grey Literature")
                    
                time.sleep(5) # DDG is more forgiving
    except Exception as e:
        print(f"[!] DDG Error: {e}")

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