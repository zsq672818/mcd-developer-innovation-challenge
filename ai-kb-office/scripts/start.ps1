# =============================================================
# AI 知识库办公平台 · 一键启动脚本（Windows 11 / PowerShell）
# 前置：已安装并启动 Docker Desktop
# 用法：
#   powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
# =============================================================

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 Docker，请先安装 Docker Desktop。" -ForegroundColor Red
    exit 1
}

# 首次运行：从模板生成后端配置文件
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host "已生成 backend\.env" -ForegroundColor Green
}

Push-Location $root
try {
    Write-Host "正在构建并启动服务（首次会下载镜像，请耐心等待）..." -ForegroundColor Cyan
    docker compose up -d --build

    Write-Host ""
    Write-Host "启动完成，请稍候片刻后访问：" -ForegroundColor Green
    Write-Host "  前端(综合看板): http://localhost:5173"
    Write-Host "  后端接口文档  : http://localhost:8000/docs"
    Write-Host ""
    Write-Host "查看日志: docker compose logs -f        （Ctrl+C 退出查看）"
    Write-Host "停止服务: docker compose down"
} finally {
    Pop-Location
}
