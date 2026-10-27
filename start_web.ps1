# 跨境智服 Agent · 本地演示启动脚本
# 用法：双击同目录的 启动演示.cmd，或直接运行本脚本

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host ''
    Write-Host '未找到虚拟环境。请先执行：' -ForegroundColor Yellow
    Write-Host '  python -m venv .venv'
    Write-Host '  .venv\Scripts\python -m pip install streamlit'
    Write-Host ''
    Read-Host '按回车退出'
    exit 1
}

$app = Join-Path $root 'web\app.py'
Write-Host ''
Write-Host '  跨境智服 Agent · 演示环境' -ForegroundColor Cyan
Write-Host '  ------------------------------------'
Write-Host '  地址：http://127.0.0.1:8501'
Write-Host '  口令：xinghe2026'
Write-Host '  按 Ctrl+C 停止服务'
Write-Host ''

Start-Sleep -Seconds 1
Start-Process 'http://127.0.0.1:8501'

Set-Location $root
& $py -m streamlit run $app --server.port 8501 --server.headless true --browser.gatherUsageStats false
