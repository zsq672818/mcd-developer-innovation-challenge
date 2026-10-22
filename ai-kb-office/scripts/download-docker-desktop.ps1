# Download Docker Desktop installer from CN-accessible mirrors
# Usage: right-click -> Run with PowerShell, or:
#   powershell -ExecutionPolicy Bypass -File .\scripts\download-docker-desktop.ps1

$ErrorActionPreference = 'Stop'
function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }

# ---------- targets ----------
$outDir = 'D:\'
$outFile = Join-Path $outDir 'DockerDesktopInstaller.exe'
$minSize = 600MB   # installer is ~620MB; anything smaller is a broken/HTML page

# CN-friendly GitHub proxy mirrors (in priority order)
$urls = @(
    'https://ghfast.top/https://github.com/tech-shrimp/docker_installer/releases/download/latest/docker_desktop_installer_windows_x86_64.exe',
    'https://ghproxy.net/https://github.com/tech-shrimp/docker_installer/releases/download/latest/docker_desktop_installer_windows_x86_64.exe',
    'https://gh-proxy.com/https://github.com/tech-shrimp/docker_installer/releases/download/latest/docker_desktop_installer_windows_x86_64.exe',
    'https://mirror.ghproxy.com/https://github.com/tech-shrimp/docker_installer/releases/download/latest/docker_desktop_installer_windows_x86_64.exe',
    'https://github.com/tech-shrimp/docker_installer/releases/download/latest/docker_desktop_installer_windows_x86_64.exe'
)

$curl = Join-Path $env:windir 'System32\curl.exe'
if (-not (Test-Path $curl)) {
    Fail "curl.exe not found at $curl (Windows 10/11 ships it by default)."
    exit 1
}

if (-not (Test-Path $outDir)) {
    Fail "Output directory $outDir does not exist."
    exit 1
}

Info "Target: $outFile"
Info "Minimum acceptable size: 600 MB"

$ok = $false
foreach ($url in $urls) {
    Info "Trying: $url"
    # -C -  : resume from where the previous attempt stopped
    # -L    : follow redirects
    # --retry 3
    & $curl -L -C - --retry 3 --connect-timeout 20 -o $outFile $url
    $code = $LASTEXITCODE

    if (Test-Path $outFile) {
        $size = (Get-Item $outFile).Length
        Info "Downloaded size: {0:N1} MB" -f ($size / 1MB)
    } else {
        $size = 0
    }

    if ($code -eq 0 -and $size -ge $minSize) {
        Ok "Download complete. Size: {0:N1} MB" -f ($size / 1MB)
        $ok = $true
        break
    } else {
        Warn "Source failed (exit=$code, size=$([math]::Round($size/1MB,1)) MB). Trying next mirror..."
    }
}

if ($ok) {
    Ok "Installer saved to: $outFile"
    Info "Next steps:"
    Info "  1. Double-click D:\DockerDesktopInstaller.exe to install (backend = WSL 2)."
    Info "  2. Reboot, then open Docker Desktop and wait for the green icon."
    Info "  3. Configure registry mirrors (Settings -> Docker Engine):"
    Info '       { "registry-mirrors": ["https://docker.m.daocloud.io","https://docker.1panel.live"] }'
    Info "  4. cd D:\workspace\ai-kb-office && .\scripts\start.ps1"
} else {
    Fail "All mirrors failed. Please download manually with a browser/Thunder:"
    foreach ($u in $urls) { Write-Host "    $u" -ForegroundColor Yellow }
    exit 1
}
