import os
import re
import sys
import time
import json
import uuid
import atexit
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import shutil
from scholarly import scholarly
from ddgs import DDGS
from discord_webhook import DiscordWebhook
from qdrant_client import QdrantClient, models
try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

# Load environment variables
load_dotenv()

def ensure_docker_running():
    """Checks if Docker engine is responsive and attempts to start it if not."""
    print("[*] Checking Docker Engine status...")
    try:
        # Check if docker is responsive
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("  -> Docker Engine is [HEALTHY]")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  [!] Docker Engine unresponsive. Attempting to start Docker Desktop...")
        docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if not os.path.exists(docker_path):
            print(f"  [!] Docker Desktop not found at {docker_path}")
            sys.exit(1)

        subprocess.Popen([docker_path])

        # Polling loop: 120s total, 10s intervals
        for attempt in range(12):
            print(f"  [*] Waiting for Docker Engine (Attempt {attempt+1}/12)...")
            time.sleep(10)
            try:
                subprocess.run(["docker", "info"], check=True, capture_output=True)
                print("  -> Docker Engine is now [HEALTHY]")
                return
            except subprocess.CalledProcessError:
                continue

        print("  [!] Docker failing to reach healthy state after 120s. Aborting.")
        sys.exit(1)

def log_system_thermals():
    """Captures CPU temperature via wmic. Returns temp in Celsius or None."""
    try:
        # Command: wmic /namespace:\\root\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature
        # Output is in tenths of Kelvin. (Total / 10) - 273.15 = Celsius
        cmd = ["wmic", "/namespace:\\\\root\\wmi", "PATH", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        if len(lines) > 1:
            raw_val = int(lines[1])
            temp_c = (raw_val / 10.0) - 273.15
            return round(temp_c, 1)
    except Exception:
        pass
    return None

# Setup paths and environment variables
RESEARCH_PATH = Path(os.getenv("RESEARCH_PATH") or ".")
LOGS_DIR = RESEARCH_PATH / "logs"
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_FILE = LOGS_DIR / "seen_sources.md"
REJECTED_LOG = LOGS_DIR / "rejected_sources.md"
TRIAGE_LOG = LOGS_DIR / "triage_log.md"
RUN_LOG = LOGS_DIR / "run_log.md"

# --- D-DRIVE MARKDOWN MIRROR ---
DB_MIRROR_DIR = Path(os.getenv("DB_MIRROR_PATH", "D:/Cyber_Physical_DBs"))

QUERY_CACHE = LOGS_DIR / "query_cache.json"
SIEVE_DROPPED_LOG = DB_MIRROR_DIR / "logs" / "sieve_dropped.log"

# --- QDRANT / LOCAL RAG CONFIG ---
QDRANT_PATH = os.getenv("QDRANT_LOCAL_PATH", str(RESEARCH_PATH / ".qdrant_db"))
TRIAGE_COLLECTION = "triage_memory"
SCOUT_COLLECTION = "scout_memory"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"  # 768-dim, matches global_resilience_vault
VECTOR_SIZE = 768


# --- EXTRACTOR HUB CONFIG ---
EXTRACTOR_HUB_URL     = "http://localhost:8003"
EXTRACTOR_HUB_ENABLED = True
EXTRACTOR_MAX_CHARS   = 3000  # Truncation limit to stay within Ollama context

# --- PERSISTENT TRIAGE TALLY ---
VERDICTS_FILE = Path("D:/Docker/extractor/stats/research_verdicts.json")

# --- DISCORD WEBHOOK CONFIG ---
WEBHOOK_MAX_RETRIES = 3  # Max attempts before giving up on a webhook post

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
if not MEMORY_FILE.exists():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write("# Scout Smart Memory Log\n")
        f.write("> Tracks every URL reviewed. Prevents duplicate evaluations across runs.\n\n")
        f.write("| Title | Date | Relevance | Rationale |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")

if not REJECTED_LOG.exists():
    with open(REJECTED_LOG, "w", encoding="utf-8") as f:
        f.write("# Rejected Sources Log\n")
        f.write("> Documents scored **LOW** by the Scout Agent — not relevant to the core thesis.\n\n")

if not TRIAGE_LOG.exists():
    with open(TRIAGE_LOG, "w", encoding="utf-8") as f:
        f.write("# Triage Log\n")
        f.write("> Documents filtered by the **Local Bouncer** (DeepSeek) before reaching Gemini confirmation.\n\n")

# --- RUN LOGGER ---
SCORE_EMOJI = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴", "SILENT_ANOMALY": "🔵"}

class RunLogger:
    """Writes structured markdown to run_log.md while also printing to the terminal."""

    def __init__(self):
        self._ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self._counts = {"evaluated": 0, "high_medium": 0, "low": 0, "triage": 0, "sieve": 0, "dropped": 0}
        self._thermal_consecutive_high = 0
        # Load lifetime verdicts from D: drive (creates defaults if file missing)
        self._lifetime = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "DROPPED": 0}
        if VERDICTS_FILE.exists():
            try:
                loaded = json.loads(VERDICTS_FILE.read_text(encoding="utf-8"))
                self._lifetime["HIGH"]    = int(loaded.get("HIGH",    0))
                self._lifetime["MEDIUM"]  = int(loaded.get("MEDIUM",  0))
                self._lifetime["LOW"]     = int(loaded.get("LOW",     0))
                self._lifetime["DROPPED"] = int(loaded.get("DROPPED", 0))
            except Exception:
                pass
        self._f = open(RUN_LOG, "a", encoding="utf-8")
        self._f.write(f"\n---\n\n## 🚀 Run — {self._ts}\n\n")
        self._f.flush()
        atexit.register(self._close)

    def log(self, msg: str):
        """Print to terminal AND append to run_log.md."""
        try:
            print(msg)
        except UnicodeEncodeError:
            # Fallback for consoles that don't support emojis/UTF-8
            print(msg.encode('ascii', 'replace').decode('ascii'))
        self._f.write(msg + "\n")
        self._f.flush()

    def section(self, icon: str, title: str):
        """Write a markdown H3 section header and check thermals."""
        self._f.write(f"\n### {icon} {title}\n\n")
        self._f.flush()
        self.check_thermals()

    def check_thermals(self):
        """Captures temp and triggers emergency shutdown if 92C for 3 checks."""
        temp = log_system_thermals()
        if temp is None:
            self._f.write("> [!] Thermal sensors unavailable via WMI.\n")
            return

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._f.write(f"> 🌡️ **Thermal Check ({ts}):** {temp}°C\n")
        self._f.flush()

        if temp >= 92:
            self._thermal_consecutive_high += 1
            self.log(f"  [!] CRITICAL HEAT: {temp}°C (Consecutive: {self._thermal_consecutive_high}/3)")
            if self._thermal_consecutive_high >= 3:
                self.log("\n" + "!" * 60)
                self.log("🚩 [PROMPT_EVOLUTION_TRIGGER]: THERMAL EMERGENCY AT 92C")
                self.log("INITIATING DATA FLUSH AND IMMEDIATE SHUTDOWN.")
                self.log("!" * 60)

                # Emergency flush to D:
                self._save_verdicts()
                self._f.write("\n### 🛑 THERMAL EMERGENCY SHUTDOWN TRIAGED\n")
                self._f.close()

                # Shutdown in 10s
                os.system("shutdown /s /t 10")
                sys.exit(1)
        else:
            self._thermal_consecutive_high = 0

    def score(self, relevance: str):
        """Track a scored result (session + lifetime)."""
        self._counts["evaluated"] += 1
        if relevance in ("HIGH", "MEDIUM"):
            self._counts["high_medium"] += 1
        elif relevance == "LOW":
            self._counts["low"] += 1
        # Increment lifetime counter
        if relevance in self._lifetime:
            self._lifetime[relevance] += 1

    def triage(self):
        self._counts["triage"] += 1

    def sieve(self):
        self._counts["sieve"] += 1

    def dropped(self):
        """Track lexicographically rejected sources."""
        self._counts["dropped"] += 1
        self._lifetime["DROPPED"] += 1

    def _save_verdicts(self):
        """Persists lifetime HIGH/MEDIUM/LOW counts to D: drive."""
        try:
            VERDICTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "HIGH":         self._lifetime["HIGH"],
                "MEDIUM":       self._lifetime["MEDIUM"],
                "LOW":          self._lifetime["LOW"],
                "DROPPED":      self._lifetime["DROPPED"],
                "last_run_ts":  self._ts
            }
            VERDICTS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[!] Could not save verdicts: {e}")

    def _close(self):
        if self._f.closed:
            return
        self._save_verdicts()
        c  = self._counts
        lt = self._lifetime
        total = lt["HIGH"] + lt["MEDIUM"] + lt["LOW"]
        self._f.write("\n#### 📊 Session Summary\n\n")
        self._f.write("| Metric | Count |\n| :--- | :--- |\n")
        self._f.write(f"| Total evaluated | {c['evaluated']} |\n")
        self._f.write(f"| 🟢🟡 HIGH / MEDIUM | {c['high_medium']} |\n")
        self._f.write(f"| 🔴 LOW / Rejected | {c['low']} |\n")
        self._f.write(f"| 🔵 Triage (Bouncer) rejections | {c['triage']} |\n")
        self._f.write(f"| ⚪ Sieve rejections | {c['sieve']} |\n\n")
        self._f.flush()
        self._f.close()
        # CMD-friendly lifetime summary
        print("")
        print("=" * 60)
        print(f"LIFETIME RESEARCH STATS ({VERDICTS_FILE.parent})")
        print("-" * 60)
        print(f"  HIGH   : {lt['HIGH']}")
        print(f"  MEDIUM : {lt['MEDIUM']}")
        print(f"  LOW    : {lt['LOW']}")
        print(f"  DROPPED: {lt['DROPPED']} (Lexical Sieve)")
        print(f"  TOTAL  : {lt['HIGH'] + lt['MEDIUM'] + lt['LOW']}")
        print(f"  Last updated: {self._ts}")
        print("=" * 60)

rl = RunLogger()

# --- QDRANT HELPERS ---

def _get_qdrant():
    """Returns a Qdrant client with both collections initialized."""
    client = QdrantClient(path=QDRANT_PATH)
    for name in (TRIAGE_COLLECTION, SCOUT_COLLECTION):
        try:
            client.get_collection(name)
        except Exception:
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
            )
    return client

def upsert_discovery(title, link, relevance, rationale, source="unknown"):
    """Embeds and upserts a discovery into scout_memory. Deduplicates by URL."""
    try:
        vector = embed_text(f"{title} {rationale}")
        if not vector:
            return
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, link))
        payload = {
            "title": title, "link": link, "relevance": relevance,
            "rationale": rationale, "source": source,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "run_ts": rl._ts
        }
        q = _get_qdrant()
        q.upsert(collection_name=SCOUT_COLLECTION,
                 points=[models.PointStruct(id=point_id, vector=vector, payload=payload)])
        q.close()
    except Exception as e:
        rl.log(f"[!] Qdrant upsert failed: {e}")

def _backfill_scout_memory():
    """One-time backfill: reads seen_sources.md and upserts historic entries."""
    if not MEMORY_FILE.exists():
        return
    try:
        q = _get_qdrant()
        existing = {str(p.id) for p in q.scroll(SCOUT_COLLECTION, limit=10000)[0]}
        count = 0
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("| ["):
                    continue
                # Parse: | [title](link) | date | badge relevance | rationale |
                parts = [p.strip() for p in line.strip().strip("|").split("|")]
                if len(parts) < 4:
                    continue
                # Extract title and link from "[title](link)"
                m = re.match(r'\[(.+?)\]\((.+?)\)', parts[0])
                if not m:
                    continue
                title, link = m.group(1), m.group(2)
                # Relevance may have emoji badge prefix
                rel_raw = parts[2].strip()
                relevance = rel_raw.split()[-1] if rel_raw else "LOW"
                rationale = parts[3].strip() if len(parts) > 3 else ""
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, link))
                if point_id in existing:
                    continue
                vector = embed_text(f"{title} {rationale}")
                if vector:
                    q.upsert(collection_name=SCOUT_COLLECTION, points=[
                        models.PointStruct(id=point_id, vector=vector,
                            payload={"title": title, "link": link, "relevance": relevance,
                                     "rationale": rationale, "source": "backfill",
                                     "date": "legacy", "run_ts": "backfill"})
                    ])
                    count += 1
        q.close()
        if count:
            rl.log(f"[+] Backfilled {count} historic entries into '{SCOUT_COLLECTION}'.")
    except Exception as e:
        rl.log(f"[!] Backfill failed: {e}")

# NOTE: _backfill_scout_memory() is called after embed_text is defined (in __main__ block)

# --- D-DRIVE MIRROR ---
import shutil

def mirror_logs():
    """Copies all markdown log files to DB_MIRROR_DIR. Silently skips if unavailable."""
    try:
        DB_MIRROR_DIR.mkdir(parents=True, exist_ok=True)
        for src in (MEMORY_FILE, REJECTED_LOG, TRIAGE_LOG, RUN_LOG):
            if src.exists():
                shutil.copy2(src, DB_MIRROR_DIR / src.name)
    except Exception:
        pass  # Mirror drive unavailable — script continues uninterrupted


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


# --- EXTRACTOR HUB HELPERS ---

def fetch_full_text(url: str):
    """Fetches full-text markdown from the Extractor Hub (port 8003).
    Returns truncated markdown string on success, None on any failure.
    CPU-only -- hub is configured with EXTRACTOR_GPU=cpu.
    """
    if not EXTRACTOR_HUB_ENABLED:
        return None
    try:
        resp = requests.post(
            f"{EXTRACTOR_HUB_URL}/extract",
            json={"uri": url},
            timeout=15,
        )
        if resp.status_code == 200:
            md = resp.json().get("markdown", "")
            return md[:EXTRACTOR_MAX_CHARS] if md else None
    except Exception:
        pass
    return None


def enrich_item(item: dict) -> dict:
    """Replaces item['snippet'] with full-text from the hub if available.
    Sets item['enriched'] = True/False so callers can log the outcome.
    """
    full_text = fetch_full_text(item.get("link", ""))
    if full_text:
        item["snippet"] = full_text
        item["enriched"] = True
    else:
        item["enriched"] = False
    return item


def recheck_low_sources(rules_text: str):
    """Re-evaluates all previously LOW-scored URLs using current prompts.
    Appends correction rows to seen_sources.md for upgrades — never edits originals.
    Fires Discord webhook for any source upgraded to HIGH or MEDIUM.
    """
    if not MEMORY_FILE.exists():
        rl.log("[Recheck] seen_sources.md not found — nothing to recheck.")
        return

    rl.log("[Recheck] Scanning seen_sources.md for LOW-scored sources...")
    low_entries = []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "| \U0001f534 LOW |" in line or "| \U0001f534 LOW" in line:
                # Parse: | [title](link) | date | badge relevance | rationale |
                m = re.match(r'\| \[(.+?)\]\((.+?)\) \|', line)
                if m:
                    low_entries.append({"title": m.group(1), "link": m.group(2)})

    if not low_entries:
        rl.log("[Recheck] No LOW entries found.")
        return

    rl.log(f"[Recheck] Found {len(low_entries)} LOW sources to re-evaluate.")
    upgraded = 0
    confirmed_low = 0

    for item in low_entries:
        title, link = item["title"], item["link"]
        rl.log(f"[Recheck] Checking: {title[:60]}")

        # Try hub enrichment first
        snippet = fetch_full_text(link) or title
        item["snippet"] = snippet
        item["enriched"] = bool(fetch_full_text(link))

        # Run through Bouncer (single-item batch)
        results = evaluate_with_ollama([item])
        rel, rat = "LOW", "Re-evaluated: still LOW."
        if results and isinstance(results, list) and len(results) > 0:
            rel = results[0].get("relevance", "LOW")
            rat = results[0].get("rationale", rat)

        if rel in ("HIGH", "MEDIUM"):
            badge = SCORE_EMOJI.get(rel, "")
            rl.log(f"[Recheck] UPGRADED: {badge} {rel}: {title[:50]}")
            # Append correction row (original LOW row preserved)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            with open(MEMORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"| [{title}]({link}) | {today} | {badge} {rel} | [RE-EVAL] {rat} |\n")
            # Notify Discord with force=True (bypass seen gate)
            notify_detailed(title, link, rel, f"[RE-EVAL] {rat}", force=True)
            upsert_discovery(title, link, rel, f"[RE-EVAL] {rat}")
            upgraded += 1
        else:
            confirmed_low += 1
            rl.log(f"[Recheck] Confirmed LOW: {title[:50]}")

        time.sleep(2)  # Be polite to Ollama between items

    print("")
    print("=" * 60)
    print("RECHECK SUMMARY")
    print("-" * 60)
    print(f"  Upgraded to HIGH/MEDIUM : {upgraded}")
    print(f"  Confirmed LOW           : {confirmed_low}")
    print(f"  Total rechecked         : {len(low_entries)}")
    print("=" * 60)


def ingest_triage_logs(qdrant):
    """Parses triage_log.md and rejected_sources.md and upserts entries into triage_memory."""
    entries = []
    for log_file in [TRIAGE_LOG, REJECTED_LOG]:
        if not log_file.exists():
            continue
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Match new format: ### 🔴 LOW — [Title](url)
                if line.startswith("### ") and "\u2014" in line:
                    entries.append(line)
                # Match legacy format: - **[date]** [title](url)
                elif line.startswith("- **["):
                    entries.append(line)

    if not entries:
        rl.log("[*] No triage log entries to ingest.")
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
        rl.log(f"[+] Ingested {len(points)} triage entries into '{TRIAGE_COLLECTION}'.")

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
    """Records a new discovery in seen_sources.md AND Qdrant scout_memory."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    badge = SCORE_EMOJI.get(relevance, "")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"| [{title}]({link}) | {today} | {badge} {relevance} | {rationale} |\n")
    rl.score(relevance)
    upsert_discovery(title, link, relevance, rationale)
    mirror_logs()

def send_webhook(message: str, title: str = "") -> bool:
    """Sends a Discord webhook with retry on rate limits and transient errors.
    Prints CMD confirmation on success. Returns True on success.
    """
    if not WEBHOOK_URL:
        return False
    label = title[:50] if title else message[:50]
    for attempt in range(1, WEBHOOK_MAX_RETRIES + 1):
        try:
            resp = DiscordWebhook(url=WEBHOOK_URL, content=message).execute()
            # DiscordWebhook.execute() returns the requests.Response object
            if resp is not None and hasattr(resp, "status_code"):
                if resp.status_code == 429:
                    # Rate limited — read retry_after and wait
                    try:
                        retry_after = resp.json().get("retry_after", 5)
                    except Exception:
                        retry_after = 5
                    rl.log(f"[Discord] Rate limited. Retrying in {retry_after}s (attempt {attempt}/{WEBHOOK_MAX_RETRIES})...")
                    time.sleep(retry_after)
                    continue
                elif resp.status_code in (200, 204):
                    print(f"[Discord] Webhook fired: {label}")
                    return True
            # Unknown/error status — fall through to retry
            rl.log(f"[Discord] Unexpected response (attempt {attempt}): {getattr(resp, 'status_code', 'N/A')}")
        except Exception as exc:
            rl.log(f"[Discord] Error on attempt {attempt}/{WEBHOOK_MAX_RETRIES}: {exc}")
        if attempt < WEBHOOK_MAX_RETRIES:
            time.sleep(5)
    rl.log(f"[!] Webhook failed after {WEBHOOK_MAX_RETRIES} attempts: {label}")
    return False


def notify_detailed(title, link, score, rationale, force=False):
    """Sends scored alert to Discord and logs the discovery.
    Set force=True to bypass the is_new_discovery gate (used by --recheck).
    """
    status_icon = "\U0001f7e2" if score == "HIGH" else "\U0001f7e1"
    if force or is_new_discovery(link):
        message = (
            f"\U0001f50d **Scout Alert:** [{status_icon} {score}]\n"
            f"**Title:** {title}\n"
            f"**Link:** <{link}>\n\n"
            f"**Agent Justification:** {rationale}"
        )
        send_webhook(message, title=title)
        if not force:
            log_discovery(title, link, score, rationale)

def log_rejection(title, link, rationale):
    """Logs low-quality hits to rejected_sources.md before marking them as seen."""
    if is_new_discovery(link):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(REJECTED_LOG, "a", encoding="utf-8") as f:
            f.write(f"### 🔴 LOW — [{title}]({link})\n")
            f.write(f"- **Date:** {today}\n")
            f.write(f"- **Rationale:** {rationale}\n\n")
        log_discovery(title, link, "LOW", rationale)

def log_triage_rejection(title, link, score, rationale):
    """Logs Local Bouncer rejections to triage_log.md."""
    if is_new_discovery(link):
        badge = SCORE_EMOJI.get(score, "")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(TRIAGE_LOG, "a", encoding="utf-8") as f:
            f.write(f"### {badge} {score} — [{title}]({link})\n")
            f.write(f"- **Date:** {today}\n")
            f.write(f"- **Rationale:** {rationale}\n\n")
        log_discovery(title, link, score, rationale)
        rl.triage()

# --- STAGE 1: PYTHON SIEVE ---
SIEVE_KEYWORDS = [
    "safety", "security", "ics", "ot", "scada", "cyber-physical",
    "breach", "emergency", "override", "risk", "resilience", "hazard",
    "industrial", "infrastructure"
]

def python_sieve(title, snippet, link="Unknown"):
    """Fast lexical zero-cost filter. Logs drops for transparency."""
    rl.sieve() # Increment scan counter
    text = (title + " " + snippet).lower()
    passed = any(kw in text for kw in SIEVE_KEYWORDS)
    if not passed:
        rl.dropped() # Increment dropped counter
        try:
            SIEVE_DROPPED_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(SIEVE_DROPPED_LOG, "a", encoding="utf-8") as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"--- {ts} ---\n")
                f.write(f"TITLE: {title}\n")
                f.write(f"URL:   {link}\n")
                f.write(f"SNIPPET: {snippet}\n\n")
        except Exception as e:
            rl.log(f"  [!] Sieve log failure: {e}")
    return passed

# --- STAGE 2: LOCAL BOUNCER (OLLAMA) ---
def evaluate_with_ollama(snippets_bulk):
    """Sends a batch of snippets to local DeepSeek."""
    # Build the serialised content block outside the f-string to avoid
    # Python misinterpreting {{...}} inside the comprehension as a set literal.
    content_list = [
        {"index": i, "title": s["title"], "content": s["snippet"]}
        for i, s in enumerate(snippets_bulk)
    ]
    content_json = json.dumps(content_list, indent=2)
    prompt = f"""
You are a research triage assistant for a study on Dynamic Risk Management in cyber-physical systems.
This research operates on the core assumption that future critical infrastructure will be comprised of hyper-interdependent cyber-physical systems.
Evaluate each search snippet using the following STRICT scoring rules:

SCORING RULES:
- HIGH (Positive Baseline): The document explicitly discusses the tension between safety and security,
  system overrides, emergency access, fail-safe/fail-open behaviors, or dynamic risk management in
  an OT/ICS or cyber-physical context as its PRIMARY focus.
- HIGH (Positive Baseline - Foundational): The document details advanced safety models,
  domain-agnostic risk frameworks, or All-Hazards/Consequence-Driven frameworks (e.g., ISO, IEC, NIST, NIMS/FEMA)
  as a primary focus.
- HIGH (Abstract/Paywall): The content appears to be an abstract or summary (e.g. from a paywalled
  academic paper). Score HIGH if it strongly implies the full document covers life-safety, OT/ICS
  risk, emergency overrides, or the safety-security intersection. Do NOT penalize abstracts for
  lacking specific architectural details — reward strong thematic signal.
- HIGH (Negative Baseline - STRUCTURAL_OMISSION): The document is a major framework, standard, or
  regulatory instrument governing OT/ICS or cyber-physical systems that is COMPLETELY SILENT on
  human life-safety, emergency egress, or physical consequences ([Safety-Blind Spot]), OR it is a
  safety/all-hazards framework that is COMPLETELY SILENT on cyber risk ([Cyber-Blind Spot]).
  Flag rationale with 🚩 [STRUCTURAL_OMISSION].
- MEDIUM: The document discusses ICS resilience, emergency workflows, or cyber-physical operations
  but only mentions safety vs. security overrides tangentially or as a secondary point.
  NOTE: If a document meets the criteria but introduces a highly novel psychological, communication,
  or risk model not easily categorized (e.g. cognitive ergonomics, operator linguistics), score it
  MEDIUM and append the 💡 [EMERGING_THEME] flag to the rationale.
- LOW: The document does not discuss complex physical safety, emergency operations, or OT/ICS
  environments. Explicitly reject standard IT cybersecurity frameworks (privacy, encryption, firewalls)
  AND routine workplace hazard compliance (OSHA ergonomics, scaffolding safety) with no tie to
  systemic resilience.

SNIPPETS:
{content_json}

Evaluate each snippet. Output your answer as a JSON object with a single key "results" containing an array:
{{"results": [
  {{"index": 0, "relevance": "HIGH" or "MEDIUM" or "LOW", "rationale": "One concise sentence. Prefix with [STRUCTURAL_OMISSION] if applicable."}}
]}}
"""
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "deepseek-r1:8b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=120)

        if response.status_code == 200:
            raw = response.json().get("response", "")
            # Scrub any <think>...</think> blocks DeepSeek may emit
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            # DeepSeek with format=json may wrap the array in {"results": [...]}
            # Try direct parse first, then extract the first JSON array found.
            try:
                parsed = json.loads(raw)
                # Primary path: object with 'results' key (matches our prompt)
                if isinstance(parsed, dict):
                    for key in ("results", "evaluations", "snippets", "output"):
                        if key in parsed and isinstance(parsed[key], list):
                            return parsed[key]
                # Fallback: model returned a bare array
                if isinstance(parsed, list):
                    return parsed
                # Last resort: regex-extract the first JSON array from the string
                match = re.search(r'\[.*?\]', raw, flags=re.DOTALL)
                if match:
                    return json.loads(match.group())
            except json.JSONDecodeError as e:
                rl.log(f"[!] Local Bouncer parse failed: {e}")
    except Exception as e:
        rl.log(f"[!] Local Bouncer offline or failed: {e}")
    return None

def process_final_score(item, rel, rat):
    """Handles the final routing for scoring."""
    title, link = item["title"], item["link"]
    badge = SCORE_EMOJI.get(rel, "")
    rl.log(f"  -> [Final] {badge} {rel}: {title[:50]}")
    if rel == "IGNORE":
        rl.log(f"  -> Skipping log for non-English source: {title[:40]}")
        return

    if rel in ["HIGH", "MEDIUM"]:
        notify_detailed(title, link, rel, rat)
    else:
        log_rejection(title, link, rat)

def process_batch(batch, rules_text):
    """Processes a batch through Stage 1.5 (Hub enrichment), Stage 2 (Ollama), Stage 3 (DeepSeek)."""
    if not batch: return
    rl.log(f"[*] Processing batch of {len(batch)} snippets through Local Bouncer...")

    # --- STAGE 1.5: EXTRACTOR HUB ENRICHMENT ---
    enriched_count = 0
    for item in batch:
        enrich_item(item)
        if item.get("enriched"):
            enriched_count += 1
    rl.log(f"[Hub] Enriched {enriched_count}/{len(batch)} items with full text "
           f"({len(batch) - enriched_count} fallback to snippet).")

    ollama_results = evaluate_with_ollama(batch)

    if ollama_results is None:
        rl.log("[!] Bouncer parse failed. Falling back to individual DeepSeek evaluation...")
        for item in batch:
            rel_data = evaluate_snippet(item["title"], item["snippet"], rules_text)
            process_final_score(item, rel_data.get("relevance", "LOW"), rel_data.get("rationale", "No rationale."))
            time.sleep(3)
        rl._save_verdicts()
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
                badge = SCORE_EMOJI.get(rel, "")
                rl.log(f"  -> [Bouncer] {badge} {rel}: {title[:50]}")

                if rel in ["LOW", "SILENT_ANOMALY"]:
                    log_triage_rejection(title, link, rel, rat)
                else:
                    # STAGE 3: DEEPSEEK CONFIRMATION
                    rl.log(f"  -> [DeepSeek Confirming] {title[:50]}...")
                    ds_data = evaluate_snippet(title, snippet, rules_text)
                    process_final_score(item, ds_data.get("relevance", "LOW"), ds_data.get("rationale", "No rationale."))
                    time.sleep(3)
    except Exception as e:
        rl.log(f"[!] Error parsing batch results: {e}")

    # Persist lifetime verdicts to D: drive after every batch
    rl._save_verdicts()

# --- GENAI CAPABILITIES ---
def generate_queries(topics):
    """Queries triage_memory for RAG context and prompts local deepseek-r1:8b to generate search queries."""
    qdrant = None
    try:
        qdrant = init_triage_collection()
        ingest_triage_logs(qdrant)

        # Retrieve the 5 most relevant high-signal findings for context
        query_vector = embed_text("high-signal safety security life-safety OT ICS silent anomaly")
        context_snippets = []
        if query_vector:
            result = qdrant.query_points(
                collection_name=TRIAGE_COLLECTION,
                query=query_vector,
                limit=5
            )
            context_snippets = [h.payload.get("text", "") for h in result.points]

        context_block = "\n".join(context_snippets) if context_snippets else "No prior triage data available."

        rl.log("[+] Initializing Local Brainstorming (DeepSeek-R1)...")
        prompt = f"""You are a research assistant for a cyber-physical resilience study.
Based on recent triage findings, generate new search queries to expand coverage.

RECENT FINDINGS:
{context_block}

TASK:
Generate exactly 3 boolean search queries for Google Scholar and 3 web queries for government grey literature.
Focus on gaps related to 'Safety over Security' and life-safety engineering principles across ALL critical
infrastructure and OT environments — including but not limited to energy, water, maritime, rail, healthcare,
and manufacturing. Identify under-explored sectors or regulatory frameworks that do not adequately address
the intersection of engineering safety and cybersecurity.

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
                rl.log("[!] Local model returned empty query lists.")
            except json.JSONDecodeError as e:
                rl.log(f"[!] JSON parse failed: {e}")
                rl.log(f"[!] Raw response snippet: {cleaned[:200]}")

    except Exception as e:
        rl.log(f"[!] Local brainstorm failed: {e}")
    finally:
        if qdrant is not None:
            qdrant.close()

    rl.log("[!] Falling back to hardcoded Master Queries.")
    return MASTER_SCHOLAR_QUERIES, MASTER_DDG_QUERIES

def evaluate_snippet(title, snippet, rules_text):
    """Uses local DeepSeek-R1 via Ollama to screen a snippet with a strict boolean filter."""
    rl.log("  [*] Using Local DeepSeek-R1 for Evaluation...")
    prompt = f"""This research operates on the core assumption that future critical infrastructure
will be comprised of hyper-interdependent cyber-physical systems.

Does this text explicitly discuss the intersection of technical security and physical safety
(e.g., cyber-physical systems, OT environments), OR does it detail advanced safety models,
domain-agnostic risk frameworks (e.g., all-hazards, ISO, IEC, NIST, NIMS/FEMA), or
systemic resilience models for high-consequence infrastructure?

(Note: Explicitly exclude documents focused solely on routine workplace hazard compliance,
occupational therapy, or basic civil building codes, unless directly tied to dynamic emergency response).

If the text is a major framework missing cyber or safety, flag with 🚩 [STRUCTURAL_OMISSION].
If it introduces novel psychological or communication models, flag with 💡 [EMERGING_THEME].

If the text is clearly an abstract, judge based on thematic signal and intent, not the presence of specific architectural keywords.

Respond ONLY with "YES" or "NO", followed by a one-sentence technical reason.

Title: {title}
Content: {snippet}"""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "deepseek-r1:8b", "prompt": prompt, "stream": False},
            timeout=60
        )
        if resp.status_code == 200:
            raw = resp.json().get("response", "")
            # Scrub DeepSeek <think>...</think> blocks
            cleaned = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            first_line = cleaned.splitlines()[0].strip() if cleaned else ""
            answer = first_line[:3].upper()
            rationale = cleaned[len(first_line):].strip() or first_line
            if answer.startswith("YES"):
                return {"relevance": "HIGH", "rationale": rationale}
            else:
                return {"relevance": "LOW", "rationale": rationale}
    except Exception as e:
        rl.log(f"[!] Local evaluation failed: {e}")
    return {"relevance": "LOW", "rationale": "Local model unavailable."}

# --- SEARCH ENGINES ---

def search_scholar(query, rules_text, limit=3):
    """Scrapes Google Scholar for academic papers."""
    rl.section("📚", f"Scholar Search")
    rl.log(f"[*] Scholar Search: {query}")
    batch = []
    try:
        search = scholarly.search_pubs(query)
        for _ in range(limit):
            paper = next(search)
            title = paper['bib'].get('title', 'Unknown')
            abstract = paper['bib'].get('abstract', '')
            link = paper.get('pub_url', 'No link')

            if link == 'No link' or not is_new_discovery(link): continue
            if not python_sieve(title, abstract, link):
                rl.log(f"  -> ⚪ Sieve rejected: {title[:50]}...")
                rl.sieve()
                continue

            batch.append({"title": title, "snippet": abstract, "link": link})
            time.sleep(5)
    except StopIteration:
        pass
    except Exception as e: rl.log(f"[!] Scholar Error: {e}")
    process_batch(batch, rules_text)

def search_ddg(query, rules_text, limit=4):
    """Scrapes DuckDuckGo for Grey Literature & government sources."""
    rl.section("🌐", f"Web Search (DDG)")
    rl.log(f"[*] Web Search (DDG): {query}")
    batch = []
    try:
        with DDGS() as duck:
            results = duck.text(query, max_results=limit)
            for res in results:
                title = res.get('title', 'Unknown')
                snippet = res.get('body', '')
                link = res.get('href', 'No link')

                if link == 'No link' or not is_new_discovery(link): continue
                if not python_sieve(title, snippet, link):
                    rl.log(f"  -> ⚪ Sieve rejected: {title[:50]}...")
                    rl.sieve()
                    continue

                batch.append({"title": title, "snippet": snippet, "link": link})
                time.sleep(2)
    except Exception as e:
        rl.log(f"[!] DDG Error: {e}")
    process_batch(batch, rules_text)

def search_google(query, rules_text, limit=4):
    """Scrapes Google Search for Grey Literature as a DDG fallback."""
    rl.section("🔎", f"Web Search (Google)")
    rl.log(f"[*] Web Search (Google): {query}")
    batch = []
    if google_search is None:
        rl.log("[!] Google Search unavailable: run `pip install googlesearch-python` to enable.")
        return
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
            if not python_sieve(title, snippet, link):
                rl.log(f"  -> ⚪ Sieve rejected: {title[:50]}...")
                rl.sieve()
                continue

            batch.append({"title": title, "snippet": snippet, "link": link})
            time.sleep(2)
    except Exception as e:
        rl.log(f"[!] Google Search Error: {e}")
    process_batch(batch, rules_text)

if __name__ == "__main__":
    ensure_docker_running()

    import argparse
    parser = argparse.ArgumentParser(description="Scout Agent: Cyber-Physical Resilience Research Pipeline")
    parser.add_argument("--refresh", action="store_true",
                        help="Bypass the local cache and force a new DeepSeek brainstorm.")
    parser.add_argument("--recheck", action="store_true",
                        help="Re-evaluate all past LOW sources with new prompts. Appends corrections; never overwrites history.")
    parser.add_argument("--overnight", action="store_true",
                        help="Preserve hardware: shut down Windows after task completion.")
    args = parser.parse_args()

    # Migrate legacy seen_sources.txt to seen_sources.md if it exists
    legacy = LOGS_DIR / "seen_sources.txt"
    if legacy.exists() and not MEMORY_FILE.exists():
        legacy.rename(MEMORY_FILE)
        rl.log("[*] Migrated seen_sources.txt -> seen_sources.md")

    # Backfill historic entries now that embed_text is defined
    _backfill_scout_memory()

    rules = load_rules()

    # --recheck mode: re-evaluate past LOW sources and exit (skip normal search)
    if args.recheck:
        rl.log("[*] --recheck mode: re-evaluating past LOW sources with current prompts...")
        recheck_low_sources(rules)
        rl.log("[*] Recheck complete. Run 'python scout.py' for a normal search pass.")
        if args.overnight:
            rl.log("[!] Overnight flag detected. Initiating hardware preservation...")
        else:
            sys.exit(0)

    if not args.recheck:
        topics_env = os.getenv("RESEARCH_TOPICS", "NIST 800-82 safety over security, FEMA Lifelines Cyber Dependency")
        topics_list = [t.strip() for t in topics_env.split(",") if t.strip()]

        # --- QUERY RESOLUTION: Cache -> DeepSeek -> Hardcoded Fallback ---
        if args.refresh:
            rl.log("[*] --refresh flag detected. Bypassing cache and requesting new queries.")
            scholar_queries, ddg_queries = generate_queries(topics_list)
        else:
            cached = load_query_cache()
            if cached:
                scholar_queries, ddg_queries = cached
                rl.log(f"[*] Loaded {len(scholar_queries)} Scholar + {len(ddg_queries)} DDG queries from cache.")
            else:
                rl.log("[*] No query cache found. Generating queries via local DeepSeek...")
                scholar_queries, ddg_queries = generate_queries(topics_list)

        rl.log("[=] Executing Pluggable Hybrid Search...")
        rl.section("🔬", "Academic Pass (Google Scholar)")

        # Academic Pass
        for sq in scholar_queries:
            search_scholar(sq, rules)

        rl.section("📰", "Grey Literature Pass (DDG + Google)")

        # Grey Literature Pass
        for dq in ddg_queries:
            search_ddg(dq, rules)
            search_google(dq, rules)

    # --- CONDITIONAL SHUTDOWN ---
    if args.overnight:
        rl.log("\n" + "="*60)
        rl.log("RESEARCH TASK COMPLETE. PRESERVING HARDWARE.")
        rl.log("System shutting down in 60s.")
        rl.log("="*60)
        # Flush everything
        rl._close()
        os.system("shutdown /s /t 60")
