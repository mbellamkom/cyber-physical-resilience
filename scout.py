import os
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
from scholarly import scholarly
import feedparser
import requests
from discord_webhook import DiscordWebhook

# Load environment variables (API keys, webhook URLs, etc.)
load_dotenv()

# Setup paths for research data and memory tracking
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
MEMORY_FILE = RESEARCH_PATH / "seen_sources.txt"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def is_new_discovery(link, refresh_days=30):
    """
    Checks if a link has been discovered recently to avoid alerting multiple times.
    """
    # If the memory file doesn't exist, it's definitely a new discovery
    if not MEMORY_FILE.exists(): return True
    
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    for line in lines:
        if "|" in line:
            seen_link, date_str = line.split("|")
            # If we've seen this exact link before...
            if seen_link == link:
                try:
                    # Check how long ago we saw it
                    last_seen = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    # If it was within the refresh window, it is not new
                    if (datetime.datetime.now() - last_seen).days < refresh_days:
                        return False 
                except ValueError: continue
                
    return True

def log_discovery(link):
    """Records a new discovery in the memory file."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{link}|{today}\n")

def notify_detailed(title, link, status="🟢"):
    """Sends a formatted alert to Discord if a new paper is found."""
    if is_new_discovery(link):
        message = f"🔍 **Discovery** [{status}]\n**Title:** {title}\n**Link:** {link}"
        
        # Trigger the Discord webhook if the URL is configured
        if WEBHOOK_URL: DiscordWebhook(url=WEBHOOK_URL, content=message).execute()
        
        # Log the discovery so we don't alert on it again soon
        log_discovery(link)

def scout_web(query, limit=3):
    """Searches Google Scholar for top papers matching the query."""
    print(f"[*] Scouting: {query}")
    try:
        search = scholarly.search_pubs(query)
        for _ in range(limit):
            paper = next(search)
            # Notify Discord that a paper needs manual review
            notify_detailed(paper['bib']['title'], paper.get('pub_url', 'No link'), "🟡 MANUAL REVIEW")
            # Sleep to respect rate limits on Scholar API
            time.sleep(15)
    except Exception as e: print(f"[!] Error: {e}")

if __name__ == "__main__":
    # Define primary research topics to scout for
    queries = ["NIST 800-82 safety over security", "FEMA Lifelines Cyber Dependency"]
    for q in queries: scout_web(q)