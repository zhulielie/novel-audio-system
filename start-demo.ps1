#Requires -Version 5.1
<#
.SYNOPSIS
    一键启动「智能小说管理系统」Demo 所需的全部服务。
.DESCRIPTION
    依次启动：
    1. Django 开发服务器（端口 8000）
    2. django-q2 异步任务队列
    3. Vue3 + Vite 前端开发服务器（端口 5176，若被占用则自动递增）

    默认账号：admin / admin
#>

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5176
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Test-PortInUse {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

# 如果默认端口被占用，自动递增前端端口
while (Test-PortInUse -Port $FrontendPort) {
    Write-Host "端口 $FrontendPort 已被占用，尝试 $($FrontendPort + 1) ..." -ForegroundColor Yellow
    $FrontendPort++
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能小说管理系统 - Demo 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "后端 API:  http://localhost:$BackendPort" -ForegroundColor Green
Write-Host "前端页面:  http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host "默认账号:  admin / admin" -ForegroundColor Green
Write-Host ""
Write-Host "将打开 3 个终端窗口，请勿关闭。" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 可在对应窗口停止服务。" -ForegroundColor Yellow
Write-Host ""

$backendCmd = "cd `"$root\backend`"; .venv\Scripts\python.exe manage.py runserver 0.0.0.0:$BackendPort"
$qclusterCmd = "cd `"$root\backend`"; .venv\Scripts\python.exe manage.py qcluster"
$frontendCmd = "cd `"$root\frontend`"; npx vite --port $FrontendPort"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $qclusterCmd -WindowStyle Normal
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host "所有服务已启动，请打开 http://localhost:$FrontendPort" -ForegroundColor Green
