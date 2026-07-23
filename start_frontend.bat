@echo off
chcp 65001 >nul
echo ==========================================
echo  启动模型性能测试平台 - 前端服务
echo  端口: 38080
echo ==========================================
cd /d "%~dp0\frontend"
echo 浏览器打开: http://localhost:38080
echo.
python serve.py
pause
