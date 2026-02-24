# =======================================================================
# setup-extractor.ps1
# Extractor Manager Service -- Windows Setup Script
#
# Requirements:
#   - Docker Desktop must be running
#   - D: drive must be available
#   - Run from the project root:
#       .\setup-extractor.ps1
# =======================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$EnvFile     = Join-Path $ProjectRoot ".env"
$ComposeFile = Join-Path $ProjectRoot "docker-compose.extractor.yml"

# -----------------------------------------------------------------------
# 0.  Pre-flight Checks
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[1/6] Running pre-flight checks..." -ForegroundColor Cyan

# Verify Docker is reachable
try {
    docker info 2>&1 | Out-Null
    Write-Host "  [OK] Docker Desktop is running." -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Docker Desktop is not running or not accessible. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Verify D: drive exists
if (-Not (Test-Path "D:\")) {
    Write-Host "  [FAIL] D: drive not found. Please ensure the D: drive is available." -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] D: drive is available." -ForegroundColor Green

# -----------------------------------------------------------------------
# 1.  Create D: Drive Directory Structure
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Creating D: drive directory structure..." -ForegroundColor Cyan

$Dirs = @(
    "D:\Docker\extractor\logs",
    "D:\Docker\extractor\stats"
)

foreach ($Dir in $Dirs) {
    if (-Not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "  [CREATED] $Dir" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] Already exists: $Dir" -ForegroundColor DarkGray
    }
}

# -----------------------------------------------------------------------
# 2.  Configure Docker Desktop to Use D: Drive (daemon.json)
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Checking Docker Desktop data-root configuration..." -ForegroundColor Cyan

$DaemonConfigPath = "$env:APPDATA\Docker\daemon.json"
$DesiredDataRoot  = "D:\\Docker\\data"

if (Test-Path $DaemonConfigPath) {
    $DaemonConfig = Get-Content $DaemonConfigPath -Raw | ConvertFrom-Json
} else {
    $DaemonConfig = [PSCustomObject]@{}
}

if ($DaemonConfig.'data-root' -ne $DesiredDataRoot) {
    Write-Host "  [INFO] Setting Docker data-root to $DesiredDataRoot ..." -ForegroundColor Yellow
    $DaemonConfig | Add-Member -MemberType NoteProperty -Name "data-root" -Value $DesiredDataRoot -Force
    $DaemonConfig | ConvertTo-Json -Depth 5 | Set-Content $DaemonConfigPath -Encoding UTF8
    Write-Host "  [OK] daemon.json updated." -ForegroundColor Green
    Write-Host "  [NOTE] Restart Docker Desktop for this change to take effect, then re-run this script." -ForegroundColor Yellow
} else {
    Write-Host "  [OK] Docker data-root is already set to $DesiredDataRoot." -ForegroundColor Green
}

# -----------------------------------------------------------------------
# 3.  Append Extractor Variables to .env (Idempotent)
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Updating .env with extractor configuration..." -ForegroundColor Cyan

if (-Not (Test-Path $EnvFile)) {
    Write-Host "  [FAIL] .env file not found at $EnvFile" -ForegroundColor Red
    exit 1
}

$EnvContent = Get-Content $EnvFile -Raw

$ExtractorBlock = @"

# 8. Extractor Manager Service
NUM_EXTRACTOR_WORKERS=2
EXTRACTOR_GPU=cpu
HOST_CODE_PATH=D:/Docker/extractor
TRACE_EVERYTHING=true
"@

# Only append if NUM_EXTRACTOR_WORKERS not already present
if ($EnvContent -notmatch "NUM_EXTRACTOR_WORKERS") {
    Add-Content -Path $EnvFile -Value $ExtractorBlock -Encoding UTF8
    Write-Host "  [OK] Extractor variables appended to .env" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Extractor variables already present in .env" -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------
# 4.  Create Docker Network (if not present)
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Ensuring Docker network 'newsbot-network' exists..." -ForegroundColor Cyan

$NetworkExists = docker network ls --filter "name=newsbot-network" --format "{{.Name}}"
if ($NetworkExists -ne "newsbot-network") {
    docker network create newsbot-network | Out-Null
    Write-Host "  [OK] Created Docker network: newsbot-network" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Network 'newsbot-network' already exists" -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------
# 5.  Start the Extractor Manager with Docker Compose
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Starting Extractor Manager Service..." -ForegroundColor Cyan

if (-Not (Test-Path $ComposeFile)) {
    Write-Host "  [FAIL] docker-compose.extractor.yml not found at $ComposeFile" -ForegroundColor Red
    exit 1
}

docker-compose -f $ComposeFile up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [FAIL] docker-compose failed to start. Check the output above for errors." -ForegroundColor Red
    exit 1
}

Write-Host "  [OK] Extractor Manager container started." -ForegroundColor Green

# -----------------------------------------------------------------------
# 6.  Health Verification (retry up to 5x, 5s apart)
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "Verifying health at http://localhost:8003/health ..." -ForegroundColor Cyan

$MaxAttempts = 5
$Attempt     = 0
$Healthy     = $false

Start-Sleep -Seconds 5   # Initial pause for container startup

while ($Attempt -lt $MaxAttempts -and -Not $Healthy) {
    $Attempt++
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Write-Host "  [OK] Health check passed (attempt $Attempt/$MaxAttempts):" -ForegroundColor Green
            Write-Host "       $($Response.Content)" -ForegroundColor White
            $Healthy = $true
        }
    } catch {
        Write-Host "  [WAIT] Attempt $Attempt/$MaxAttempts -- service not ready yet. Retrying in 5s..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-Not $Healthy) {
    Write-Host ""
    Write-Host "  [FAIL] Service did not respond after $MaxAttempts attempts." -ForegroundColor Red
    Write-Host "         Run: docker logs extractor-manager -- to inspect startup errors." -ForegroundColor Yellow
    exit 1
}

# -----------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "  Extractor Manager Service setup complete!" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "  Endpoints:" -ForegroundColor Cyan
Write-Host "     Health:  http://localhost:8003/health" -ForegroundColor White
Write-Host "     Stats:   http://localhost:8003/stats" -ForegroundColor White
Write-Host "     Extract: POST http://localhost:8003/extract" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "  D: Drive Paths:" -ForegroundColor Cyan
Write-Host "     Logs:    D:\Docker\extractor\logs" -ForegroundColor White
Write-Host "     Stats:   D:\Docker\extractor\stats" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "  Configuration (from .env):" -ForegroundColor Cyan
Write-Host "     NUM_EXTRACTOR_WORKERS = 2  (4GB VRAM stays free for Ollama)" -ForegroundColor White
Write-Host "     EXTRACTOR_GPU         = cpu" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "  Useful commands:" -ForegroundColor Cyan
Write-Host "     docker logs -f extractor-manager" -ForegroundColor White
Write-Host "     docker-compose -f docker-compose.extractor.yml down" -ForegroundColor White
Write-Host "=======================================================================" -ForegroundColor Cyan
