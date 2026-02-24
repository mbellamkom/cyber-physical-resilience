# -----------------------------------------------------------------------
# Dockerfile -- Extractor Hub
# Builds hub.py as a self-contained FastAPI + trafilatura service.
#
# Build (from project root):
#   docker-compose -f docker-compose.extractor.yml up --build -d
#
# Or manually:
#   docker build -t extractor-manager:latest .
#   docker run -p 8003:8003 extractor-manager:latest
# -----------------------------------------------------------------------

FROM python:3.11-slim

# Metadata
LABEL maintainer="Cyber-Physical Resilience Project"
LABEL description="Self-contained content extraction hub (FastAPI + trafilatura)"

# ---- System dependencies ------------------------------------------------
# lxml and trafilatura need these C libs for fast HTML parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ------------------------------------------------
WORKDIR /app

# Copy only requirements first so Docker can cache this layer
COPY requirements-hub.txt ./
RUN pip install --no-cache-dir -r requirements-hub.txt

# ---- Application code ---------------------------------------------------
COPY hub.py ./

# ---- Runtime directories (overridden by volume mounts at run time) ------
RUN mkdir -p /data/logs /data/stats

# ---- Expose port --------------------------------------------------------
EXPOSE 8003

# ---- Healthcheck (Docker-native, supplements /health endpoint) ----------
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

# ---- Entrypoint ---------------------------------------------------------
CMD ["uvicorn", "hub:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
