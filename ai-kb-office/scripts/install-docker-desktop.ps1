# =============================================================
# Docker Desktop: fast download + auto install + CN registry mirror
# Works on Windows 11 with PowerShell 5.1 and PowerShell 7.x
# (ASCII-only on purpose: avoids GBK/UTF-8 mojibake on PS 5.1)
# Usage (Admin PowerShell):
#   powershell -ExecutionPolicy Bypass -File .\scripts\install-docker-desktop.ps1
# Or just double-click install-docker-desktop.bat in the project root.
# =============================================================

$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

# ---------- 0. Admin check (auto elevate) ----------
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Warn "Administrator rights required. Re-launching elevated..."
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    )
    exit 0
}

# ---------- 1. Check WSL2 (prerequisite of Docker Desktop) ----------
Info "Checking WSL2 status ..."
$hasWsl = [bool](Get-Command wsl -ErrorAction SilentlyContinue)
if (-not $hasWsl) {
    Warn "WSL not found. Running: wsl --install (a reboot is required afterwards)"
    wsl --install
    Fail "WSL install triggered. Please REBOOT the PC, then run this script again."
    exit 0
}
wsl --status *> $null
if ($LASTEXITCODE -ne 0) {
    Warn "WSL is not initialized yet. Running: wsl --install ..."
    wsl --install
    Fail "Please REBOOT the PC, then run this script again."
    exit 0
}
Ok "WSL2 is ready"

# ---------- 2. Download installer (multi-mirror with retry) ----------
$arch = $env:PROCESSOR_ARCHITECTURE
if ($arch -eq 'ARM64') {
    $asset = 'docker_desktop_installer_windows_arm64.exe'
} else {
    $asset = 'docker_desktop_installer_windows_x86_64.exe'
}
$rawUrl = "https://github.com/tech-shrimp/docker_installer/releases/download/latest/$asset"

# Try CN accelerator proxies first, then the official link
$sources = @(
    "https://ghfast.top/$rawUrl",
    "https://ghproxy.net/$rawUrl",
    "https://gh-proxy.com/$rawUrl",
    $rawUrl
)

$outDir = Join-Path $env:USERPROFILE 'Downloads'
if (-not (Test-Path $outDir)) { $outDir = $env:TEMP }
$outFile = Join-Path $outDir 'DockerDesktopInstaller.exe'

Info "Downloading Docker Desktop installer (about 620MB, resumable) ..."
Info "Save to: $outFile"

$downloaded = $false
foreach ($url in $sources) {
    Info "Trying source: $url"
    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        & curl.exe -L -C - --retry 3 --retry-delay 3 --connect-timeout 20 -o "$outFile" "$url"
    } else {
        try { Invoke-WebRequest -Uri $url -OutFile "$outFile" -UseBasicParsing } catch { }
    }
    if (Test-Path $outFile) {
        $sizeMB = (Get-Item $outFile).Length / 1MB
        if ($sizeMB -gt 300) {
            Ok ("Download complete: {0:N1} MB" -f $sizeMB)
            $downloaded = $true
            break
        }
        Warn ("File too small from this source ({0:N1} MB), trying next" -f $sizeMB)
        Remove-Item $outFile -Force -ErrorAction SilentlyContinue
    } else {
        Warn "Download failed from this source, trying next"
    }
}
if (-not $downloaded) {
    Fail "All download sources failed. Download manually with a browser or Thunder from any of:"
    foreach ($u in $sources) { Write-Host "  $u" }
    exit 1
}

# ---------- 3. Silent install ----------
Info "Installing Docker Desktop (silent, accept license, WSL2 backend) ..."
Start-Process -FilePath $outFile -Wait -ArgumentList @(
    'install', '--quiet', '--accept-license', '--backend=wsl-2'
)
Ok "Docker Desktop installed"

# ---------- 4. Configure CN registry mirrors ----------
Info "Configuring CN registry mirrors ..."
$cfgDir = Join-Path $env:USERPROFILE '.docker'
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$cfgFile = Join-Path $cfgDir 'daemon.json'
$config = @{ 'registry-mirrors' = @('https://docker.m.daocloud.io', 'https://docker.1panel.live') }
Set-Content -Path $cfgFile -Value ($config | ConvertTo-Json -Depth 5) -Encoding UTF8
Ok "Mirror config written: $cfgFile"

Write-Host ""
Ok "All done. Open Docker Desktop manually, wait until its icon turns green (Running), then run:"
Write-Host "     .\scripts\start.ps1" -ForegroundColor Cyan
Warn "If mirrors do not take effect: Docker Desktop -> Settings -> Docker Engine, make sure the registry-mirrors above are present, then click Apply and Restart."
