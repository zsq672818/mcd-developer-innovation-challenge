# =============================================================
# AI 知识库办公平台 · 环境自检脚本（Windows 11 / PowerShell）
# 用法：右键“使用 PowerShell 运行”，或在 PowerShell 中执行：
#   powershell -ExecutionPolicy Bypass -File .\scripts\check-env.ps1
# =============================================================

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "=== AI 知识库办公平台 · 环境自检 ===" -ForegroundColor Cyan
Write-Host ("操作系统: {0}" -f (Get-CimInstance Win32_OperatingSystem).Caption)
Write-Host ("PowerShell: {0}" -f $PSVersionTable.PSVersion.ToString())
Write-Host ""

$missing = @()

# ---- 1. WSL2（Docker Desktop 的前置依赖） ----
$wslOut = (wsl --status 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK]   WSL2 已启用" -ForegroundColor Green
} else {
    Write-Host "[缺失] WSL2 未启用" -ForegroundColor Yellow
    $missing += "WSL2"
}

# ---- 2. Docker Desktop ----
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host ("[OK]   Docker: {0}" -f (docker --version)) -ForegroundColor Green
    $info = (docker info 2>&1 | Out-String)
    if ($info -match 'Server Version') {
        Write-Host "[OK]   Docker 守护进程正在运行" -ForegroundColor Green
    } else {
        Write-Host "[缺失] Docker 已安装但未启动（请先打开 Docker Desktop 并等待图标变绿）" -ForegroundColor Yellow
        $missing += "Docker 未启动"
    }
} else {
    Write-Host "[缺失] 未安装 Docker Desktop" -ForegroundColor Yellow
    $missing += "Docker Desktop"
}

# ---- 3. 可选组件（Docker 方式下非必需，仅作参考） ----
foreach ($t in 'node', 'git', 'python') {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Write-Host ("[参考] {0} 已安装" -f $t) -ForegroundColor DarkGray
    } else {
        Write-Host ("[参考] {0} 未安装（Docker 方式不需要）" -f $t) -ForegroundColor DarkGray
    }
}

Write-Host ""
if ($missing.Count -eq 0) {
    Write-Host "结论：环境已就绪，可以执行 .\scripts\start.ps1 启动 demo。" -ForegroundColor Green
} else {
    Write-Host ("结论：还缺少 -> {0}" -f ($missing -join "、")) -ForegroundColor Yellow
    Write-Host "请按下列顺序安装："
    Write-Host "  1) 以管理员身份运行 PowerShell，执行： wsl --install   然后重启电脑"
    Write-Host "  2) 下载并安装 Docker Desktop： https://www.docker.com/products/docker-desktop/"
    Write-Host "  3) 启动 Docker Desktop，等待其状态显示为 Running，再重新运行本脚本"
}
