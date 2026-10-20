# =============================================================
# AI KB Office Platform - one-click start (Windows 11 / PowerShell)
# Prerequisite: Docker Desktop installed and running
# (ASCII-only on purpose: avoids GBK/UTF-8 mojibake on PS 5.1)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
# =============================================================

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# First run: create backend config from the template
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host "Created backend\.env" -ForegroundColor Green
}

Push-Location $root
try {
    Write-Host "Building and starting services (first run downloads images, please wait) ..." -ForegroundColor Cyan
    docker compose up -d --build

    Write-Host ""
    Write-Host "Started. Open these in a few seconds:" -ForegroundColor Green
    Write-Host "  Frontend (Dashboard): http://localhost:5173"
    Write-Host "  Backend API docs    : http://localhost:8000/docs"
    Write-Host ""
    Write-Host "Logs: docker compose logs -f   (Ctrl+C to exit)"
    Write-Host "Stop: docker compose down"
} finally {
    Pop-Location
}
