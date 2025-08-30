@echo off
echo 🎯 批量下载系统前端启动器
echo ==================================================

echo 📦 安装依赖包...
call npm install

echo.
echo 🚀 启动前端开发服务器...
echo 💡 前端地址: http://localhost:5173
echo 💡 确保后端服务器已启动: http://localhost:8000
echo.

call npm run dev

pause
