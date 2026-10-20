# =============================================================
# AI KB Office Platform - environment check (Windows 11 / PowerShell)
# (ASCII-only on purpose: avoids GBK/UTF-8 mojibake on PS 5.1)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\check-env.ps1
# =============================================================

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "=== AI KB Office Platform - Environment Check ===" -ForegroundColor Cyan
Write-Host ("OS         : {0}" -f (Get-CimInstance Win32_OperatingSystem).Caption)
Write-Host ("PowerShell : {0}" -f $PSVersionTable.PSVersion.ToString())
Write-Host ""

$missing = @()

# ---- 1. WSL2 (prerequisite of Docker Desktop) ----
$wslOut = (wsl --status 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) {
    Write-Host "[ OK ] WSL2 enabled" -ForegroundColor Green
} else {
    Write-Host "[MISS] WSL2 not enabled" -ForegroundColor Yellow
    $missing += "WSL2"
}

# ---- 2. Docker Desktop ----
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host ("[ OK ] Docker: {0}" -f (docker --version)) -ForegroundColor Green
    $info = (docker info 2>&1 | Out-String)
    if ($info -match 'Server Version') {
        Write-Host "[ OK ] Docker daemon is running" -ForegroundColor Green
    } else {
        Write-Host "[MISS] Docker installed but not running (open Docker Desktop and wait until green)" -ForegroundColor Yellow
        $missing += "Docker not running"
    }
} else {
    Write-Host "[MISS] Docker Desktop not installed" -ForegroundColor Yellow
    $missing += "Docker Desktop"
}

# ---- 3. Optional tools (not required for the Docker way) ----
foreach ($t in 'node', 'git', 'python') {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Write-Host ("[REF ] {0} installed" -f $t) -ForegroundColor DarkGray
    } else {
        Write-Host ("[REF ] {0} not installed (not required for the Docker way)" -f $t) -ForegroundColor DarkGray
    }
}

Write-Host ""
if ($missing.Count -eq 0) {
    Write-Host "Result: environment is ready. Run .\scripts\start.ps1 to start the demo." -ForegroundColor Green
} else {
    Write-Host ("Result: missing -> {0}" -f ($missing -join ", ")) -ForegroundColor Yellow
    Write-Host "Install in this order:"
    Write-Host "  1) In Admin PowerShell run: wsl --install   then reboot the PC"
    Write-Host "  2) Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    Write-Host "  3) Start Docker Desktop, wait until Running, then run this script again"
}
