---
description: Set up and run the Extractor Manager Service (Docker, D: drive, CPU-only)
---

# Extractor Manager Service — Setup Workflow

## Pre-flight Requirements

Before running, ensure:
- Docker Desktop is **running**
- Your **D: drive** is accessible (`Test-Path D:\` should return `True`)
- The `extractor-manager:latest` Docker image has been built or pulled
- You are in the project root directory: `C:\Users\mbell\Documents\Cyber-Physical-Resilience`

---

## Step 1 — Run the Setup Script

This single script handles all setup steps: creates D: drive directories, configures Docker data-root, appends `.env` variables, creates the Docker network, starts the service, and verifies health.

```powershell
.\setup-extractor.ps1
```

**Expected output for a clean first run:**
```
[1/6] Running pre-flight checks...  ✅ Docker Desktop is running.  ✅ D: drive is available.
[2/6] Creating D: drive directory structure...  ✅ Created: D:\Docker\extractor\logs  ✅ Created: D:\Docker\extractor\stats
[3/6] Checking Docker Desktop data-root configuration...  ✅ daemon.json updated.
[4/6] Updating .env with extractor configuration...  ✅ Extractor variables appended to .env
[5/6] Ensuring Docker network 'newsbot-network' exists...  ✅ Created Docker network: newsbot-network
[6/6] Starting Extractor Manager Service...  ✅ Extractor Manager container started.
✅ Health check passed: {"status":"healthy","ready_workers":2}
```

> **⚠️ If Docker data-root was just changed:** The script will prompt you to restart Docker Desktop. Do so, then re-run `.\setup-extractor.ps1`.

---

## Step 2 — Verify the Service

After the script completes, confirm the service is healthy:

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing | Select-Object -ExpandProperty Content

# Expected: {"status":"healthy","ready_workers":2}

# Full stats
Invoke-WebRequest -Uri "http://localhost:8003/stats" -UseBasicParsing | Select-Object -ExpandProperty Content
```

Verify logs are writing to D: drive:
```powershell
Get-ChildItem D:\Docker\extractor\logs
Get-ChildItem D:\Docker\extractor\stats
```

---

## Step 3 — Commit the New Files

**Tier A (Autonomous) — commit these files immediately:**

```powershell
git add setup-extractor.ps1 docker-compose.extractor.yml .env
git commit -m "feat(extractor): add Extractor Manager setup script and compose file"
```

**Tier B — Restricted Zone file (this workflow):**
This file (`.agent/workflows/extractor-setup.md`) was written under an `APPROVED` authorization from the human researcher. It should be committed manually after review.

---

## Useful Management Commands

```powershell
# View live logs
docker logs -f extractor-manager

# Stop the service
docker-compose -f docker-compose.extractor.yml down

# Restart the service
docker-compose -f docker-compose.extractor.yml restart

# Monitor worker activity
docker ps --filter "name=extractor"

# Watch real-time stats (run in a separate PowerShell window)
while ($true) { Invoke-WebRequest -Uri "http://localhost:8003/stats" -UseBasicParsing | Select-Object -ExpandProperty Content; Start-Sleep 5 }
```

---

## Configuration Reference

| Variable | Value | Reason |
|---|---|---|
| `NUM_EXTRACTOR_WORKERS` | `2` | Keeps NVIDIA VRAM free for Ollama |
| `EXTRACTOR_GPU` | `cpu` | Disables GPU allocation entirely |
| `HOST_CODE_PATH` | `D:/Docker/extractor` | D: drive storage root |
| `TRACE_EVERYTHING` | `true` | Full trace logging enabled |

**Volume Mounts:**
| Host Path | Container Path | Purpose |
|---|---|---|
| `D:\Docker\extractor\logs` | `/data/logs` | Manager logs (daily rotation) |
| `D:\Docker\extractor\stats` | `/data/stats` | `extractor_manager_lifetime.json` |
| `\\.\pipe\docker_engine` | `/var/run/docker.sock` | Docker daemon control |

---

## Enabling GPU (Future)

When you are ready to allocate a GPU:

1. Edit `.env`: change `EXTRACTOR_GPU=cpu` → `EXTRACTOR_GPU=0`
2. Edit `docker-compose.extractor.yml`: update the environment override accordingly
3. Restart: `docker-compose -f docker-compose.extractor.yml restart`
