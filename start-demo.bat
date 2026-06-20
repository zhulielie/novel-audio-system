@echo off
chcp 65001 >nul
title 智能小说管理系统 - Demo 启动器
echo 正在启动 Demo 全部服务...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0start-demo.ps1" %*
echo.
echo 启动器已退出，服务窗口仍然保持运行。
pause
