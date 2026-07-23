@echo off
chcp 65001 >nul
echo ==========================================
echo  启动模型性能测试平台 - 后端服务
echo  端口: 38081
echo ==========================================
cd /d "%~dp0"
venv\Scripts\python.exe -m backend.main
pause
