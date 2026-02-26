"""
hub.py -- Self-Contained Extractor Hub
FastAPI service on port 8003 that extracts web content to Markdown.

Endpoints:
    GET  /health   -- liveness check (used by setup-extractor.ps1)
    GET  /stats    -- session and lifetime extraction counts
    POST /extract  -- {"uri": "https://..."} -> {"markdown": "...", "uri": "..."}
"""

import json
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import socket
import ipaddress
from urllib.parse import urlparse
import trafilatura
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

NUM_WORKERS = int(os.getenv("NUM_EXTRACTOR_WORKERS", "2"))


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


@app.get("/stats")
async def stats():
    """Return session and lifetime extraction counts, persist to disk."""
    # Merge session into lifetime before returning
    lifetime_stats["extractions_completed"] = (
        load_lifetime_stats()["extractions_completed"]
        + session_stats["extractions_completed"]
    )
    save_lifetime_stats(lifetime_stats)

    return {
        "session": {"extractions_completed": session_stats["extractions_completed"]},
        "lifetime": {"extractions_completed": lifetime_stats["extractions_completed"]},
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


@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    """
    Download and extract the main text content from a URL.
    Returns Markdown via trafilatura.
    """
    uri = request.uri.strip()

    if not is_safe_url(uri):
        logger.warning("Blocked unsafe/internal URI: %s", uri)
        raise HTTPException(status_code=400, detail="Invalid or restricted URI.")

    logger.info("Extracting: %s", uri)

    try:
        # Fetch and extract -- include_tables keeps structured data
        downloaded = trafilatura.fetch_url(uri)
        if downloaded is None:
            logger.error("Failed to fetch URL: %s", uri)
            raise HTTPException(status_code=500, detail="Failed to fetch URL")

        markdown = trafilatura.extract(
            downloaded,
            output_format="markdown",
            include_tables=True,
            include_links=True,
            favor_recall=True,   # maximise content coverage
        )

        if not markdown:
            logger.warning("No extractable content at: %s", uri)
            raise HTTPException(status_code=500, detail="No content extracted")

        session_stats["extractions_completed"] += 1
        logger.info(
            "Extracted %d chars from %s (session total: %d)",
            len(markdown),
            uri,
            session_stats["extractions_completed"],
        )
        return ExtractResponse(markdown=markdown, uri=uri)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error extracting %s: %s", uri, exc)
        raise HTTPException(status_code=500, detail="Extraction failed") from exc


# ---------------------------------------------------------------------------
# Entry point (for local dev; Docker uses uvicorn CLI)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("hub:app", host="0.0.0.0", port=8003, reload=False)
