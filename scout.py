import os
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
from scholarly import scholarly
import feedparser
import requests
from discord_webhook import DiscordWebhook

load_dotenv()
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
MEMORY_FILE = RESEARCH_PATH / "seen_sources.txt"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def is_new_discovery(link, refresh_days=30):
    if not MEMORY_FILE.exists(): return True
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        if "|" in line:
            seen_link, date_str = line.split("|")
            if seen_link == link:
                try:
                    last_seen = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    if (datetime.datetime.now() - last_seen).days < refresh_days:
                        return False 
                except ValueError: continue
    return True

def log_discovery(link):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{link}|{today}\n")

def notify_detailed(title, link, status="🟢"):
    if is_new_discovery(link):
        message = f"🔍 **Discovery** [{status}]\n**Title:** {title}\n**Link:** {link}"
        if WEBHOOK_URL: DiscordWebhook(url=WEBHOOK_URL, content=message).execute()
        log_discovery(link)

def scout_web(query, limit=3):
    print(f"[*] Scouting: {query}")
    try:
        search = scholarly.search_pubs(query)
        for _ in range(limit):
            paper = next(search)
            notify_detailed(paper['bib']['title'], paper.get('pub_url', 'No link'), "🟡 MANUAL REVIEW")
            time.sleep(15)
    except Exception as e: print(f"[!] Error: {e}")

if __name__ == "__main__":
    queries = ["NIST 800-82 safety over security", "FEMA Lifelines Cyber Dependency"]
    for q in queries: scout_web(q)