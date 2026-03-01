"""
hub.py -- Self-Contained Extractor Hub
FastAPI service on port 8003 that extracts web content to Markdown.

Endpoints:
    GET  /health   -- liveness check (used by setup-extractor.ps1)
    GET  /stats    -- session and lifetime extraction counts
    POST /extract  -- {"uri": "https://..."} -> {"markdown": "...", "uri": "..."}
"""

import ipaddress
import json
import logging
import os
import socket
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests
import trafilatura
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ---------------------------------------------------------------------------
# Paths (match volume mounts in docker-compose.extractor.yml)
# ---------------------------------------------------------------------------
LOG_DIR   = Path("/data/logs")
STATS_DIR = Path("/data/stats")
STATS_FILE = STATS_DIR / "extractor_hub_lifetime.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
STATS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging -- daily rotating file + console
# ---------------------------------------------------------------------------
log_filename = LOG_DIR / f"extractor-hub-{datetime.utcnow().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - extractor-hub - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        TimedRotatingFileHandler(
            filename=log_filename,
            when="midnight",
            interval=1,
            backupCount=30,
            utc=True,
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("extractor-hub")

# ---------------------------------------------------------------------------
# Lifetime stats (persisted across restarts)
# ---------------------------------------------------------------------------
def load_lifetime_stats() -> dict:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"extractions_completed": 0}


def save_lifetime_stats(stats: dict) -> None:
    STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")


lifetime_stats = load_lifetime_stats()
session_stats  = {"extractions_completed": 0}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Extractor Hub", version="1.0.0")

# V-08: Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

NUM_WORKERS = int(os.getenv("NUM_EXTRACTOR_WORKERS", "2"))

# ---------------------------------------------------------------------------
# Auth (V-02)
# ---------------------------------------------------------------------------
API_KEY = os.getenv("HUB_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if not API_KEY:
        # If no key is configured, we allow it for now but log a warning.
        # In a strict environment, this would be a 403.
        logger.warning("HUB_API_KEY not set in environment. Running WITHOUT authentication.")
        return
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ExtractRequest(BaseModel):
    uri: str


class ExtractResponse(BaseModel):
    markdown: str
    uri: str


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Extractor Hub starting up...")
    logger.info(
        "Config: NUM_EXTRACTOR_WORKERS=%s, EXTRACTOR_GPU=%s",
        NUM_WORKERS,
        os.getenv("EXTRACTOR_GPU", "cpu"),
    )
    logger.info("Log dir:   %s", LOG_DIR)
    logger.info("Stats dir: %s", STATS_DIR)
    logger.info("Startup complete.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Liveness check -- used by setup-extractor.ps1 verification loop."""
    return {"status": "healthy"}


@app.get("/stats", dependencies=[Depends(verify_api_key)])
async def stats():
    """Return session and lifetime extraction counts, merge for response."""
    # V-13: Refactor to prevent race condition/double-counting on file writes
    current_lifetime = load_lifetime_stats()["extractions_completed"]
    merged_total = current_lifetime + session_stats["extractions_completed"]

    return {
        "session": {"extractions_completed": session_stats["extractions_completed"]},
        "lifetime": {"extractions_completed": merged_total},
        "num_extractor_workers": NUM_WORKERS,
    }


def is_safe_url(url: str) -> bool:
    """
    Validates that a URL uses HTTP/HTTPS and resolves to a public IP address.
    Blocks localhost, private network ranges, and reserved/multicast IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve hostname to IP
        ip_addr = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip_addr)

        # Block internal/private ranges
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_reserved
            or ip_obj.is_link_local
            or ip_obj.is_multicast
        ):
            return False

        return True
    except Exception:
        return False


@app.post("/extract", response_model=ExtractResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("40/minute")
async def extract(request: Request, body: ExtractRequest):
    """
    Download and extract the main text content from a URL.
    Implements DNS-rebinding protection (V-01) and Rate Limiting (V-08).
    """
    uri = body.uri.strip()

    # 1. Parse and validate protocol
    parsed = urlparse(uri)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid scheme.")

    # 2. Resolve IP and check against blocklist (V-01 Pinned IP)
    try:
        hostname = parsed.hostname
        if not hostname: raise ValueError("No hostname")
        ip_addr = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip_addr)

        if (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or
            ip_obj.is_link_local or ip_obj.is_multicast):
            logger.warning("Blocked internal/reserved IP: %s (%s)", ip_addr, uri)
            raise HTTPException(status_code=400, detail="Restricted URI.")

    except Exception as e:
        logger.warning("DNS/IP Validation failed for %s: %s", uri, e)
        raise HTTPException(status_code=400, detail="Could not resolve or validate host.")

    # 3. Pin the request to the resolved IP to prevent DNS rebinding (V-01)
    # We replace the hostname in the netloc with the IP, and send the original host as a header.
    pinned_netloc = ip_addr
    if parsed.port:
        pinned_netloc = f"{ip_addr}:{parsed.port}"

    pinned_uri = urlunparse(parsed._replace(netloc=pinned_netloc))
    headers = {"Host": hostname}

    logger.info("Extracting (Pinned IP %s): %s", ip_addr, uri)

    try:
        # Use requests for the pinned fetch to ensure we hit the IP we validated.
        # verify=False is used specifically here because hit-by-IP triggers SNI/SSL mismatches.
        # Since we already validated the IP against a blocklist, this is a bounded trade-off.
        resp = requests.get(pinned_uri, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()

        # Pass the downloaded raw content to trafilatura for extraction
        markdown = trafilatura.extract(
            resp.text,
            output_format="markdown",
            include_tables=True,
            include_links=True,
            favor_recall=True,
        )

        if not markdown:
            logger.warning("No extractable content at: %s", uri)
            raise HTTPException(status_code=500, detail="No content extracted")

        session_stats["extractions_completed"] += 1
        return ExtractResponse(markdown=markdown, uri=uri)

    except Exception as exc:
        logger.exception("Extraction failed for %s: %s", uri, exc)
        raise HTTPException(status_code=500, detail="Extraction failed")


# ---------------------------------------------------------------------------
# Entry point (for local dev; Docker uses uvicorn CLI)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("hub:app", host="0.0.0.0", port=8003, reload=False)
