# =============================================================
# Docker Desktop 加速下载 + 自动安装 + 国内镜像加速（Windows 11）
# 用法：管理员 PowerShell 执行
#   powershell -ExecutionPolicy Bypass -File .\scripts\install-docker-desktop.ps1
# 或直接双击根目录的 install-docker-desktop.bat
# =============================================================

$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[信息] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[完成] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[注意] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[错误] $m" -ForegroundColor Red }

# ---------- 0. 管理员权限（自动提权） ----------
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Warn "需要管理员权限，正在以管理员身份重新启动本脚本..."
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    )
    exit 0
}

# ---------- 1. 检查 WSL2（Docker Desktop 前置依赖） ----------
Info "检查 WSL2 状态..."
$hasWsl = [bool](Get-Command wsl -ErrorAction SilentlyContinue)
if (-not $hasWsl) {
    Warn "未检测到 WSL，正在执行 wsl --install（完成后需要重启电脑）..."
    wsl --install
    Fail "WSL 安装已触发，请【重启电脑】后再次运行本脚本。"
    exit 0
}
wsl --status *> $null
if ($LASTEXITCODE -ne 0) {
    Warn "WSL 尚未正确初始化，正在执行 wsl --install ..."
    wsl --install
    Fail "请【重启电脑】后再次运行本脚本。"
    exit 0
}
Ok "WSL2 已就绪"

# ---------- 2. 下载安装包（多镜像源自动重试） ----------
$arch = $env:PROCESSOR_ARCHITECTURE
if ($arch -eq 'ARM64') {
    $asset = 'docker_desktop_installer_windows_arm64.exe'
} else {
    $asset = 'docker_desktop_installer_windows_x86_64.exe'
}
$rawUrl = "https://github.com/tech-shrimp/docker_installer/releases/download/latest/$asset"

# 依次尝试：国内加速代理 -> 官方直链
$sources = @(
    "https://ghfast.top/$rawUrl",
    "https://ghproxy.net/$rawUrl",
    "https://gh-proxy.com/$rawUrl",
    $rawUrl
)

$outDir = Join-Path $env:USERPROFILE 'Downloads'
if (-not (Test-Path $outDir)) { $outDir = $env:TEMP }
$outFile = Join-Path $outDir 'DockerDesktopInstaller.exe'

Info "开始下载 Docker Desktop 安装包（约 620MB，支持断点续传）..."
Info "保存位置：$outFile"

$downloaded = $false
foreach ($url in $sources) {
    Info "尝试下载源：$url"
    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        & curl.exe -L -C - --retry 3 --retry-delay 3 --connect-timeout 20 -o "$outFile" "$url"
    } else {
        try { Invoke-WebRequest -Uri $url -OutFile "$outFile" -UseBasicParsing } catch { }
    }
    if (Test-Path $outFile) {
        $sizeMB = (Get-Item $outFile).Length / 1MB
        if ($sizeMB -gt 300) {
            Ok ("下载完成：{0:N1} MB" -f $sizeMB)
            $downloaded = $true
            break
        }
        Warn ("该源文件偏小（{0:N1} MB），换下一个源" -f $sizeMB)
        Remove-Item $outFile -Force -ErrorAction SilentlyContinue
    } else {
        Warn "该源下载失败，换下一个源"
    }
}
if (-not $downloaded) {
    Fail "所有下载源均失败。请用浏览器/迅雷手动打开以下任意地址下载，再双击安装："
    foreach ($u in $sources) { Write-Host "  $u" }
    exit 1
}

# ---------- 3. 静默安装 ----------
Info "开始安装 Docker Desktop（静默模式 / 接受许可协议 / WSL2 后端）..."
Start-Process -FilePath $outFile -Wait -ArgumentList @(
    'install', '--quiet', '--accept-license', '--backend=wsl-2'
)
Ok "Docker Desktop 安装完成"

# ---------- 4. 配置国内镜像加速器 ----------
Info "配置国内镜像加速器（registry-mirrors）..."
$cfgDir = Join-Path $env:USERPROFILE '.docker'
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$cfgFile = Join-Path $cfgDir 'daemon.json'
$config = @{ 'registry-mirrors' = @('https://docker.m.daocloud.io', 'https://docker.1panel.live') }
Set-Content -Path $cfgFile -Value ($config | ConvertTo-Json -Depth 5) -Encoding UTF8
Ok "已写入加速器配置：$cfgFile"

Write-Host ""
Ok "全部完成。请手动打开 Docker Desktop，等任务栏图标变为绿色(Running)后，执行："
Write-Host "     .\scripts\start.ps1" -ForegroundColor Cyan
Warn "若加速器未生效：Docker Desktop -> Settings -> Docker Engine，确认其中包含上面的 registry-mirrors 内容后 Apply & Restart"
