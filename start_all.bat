@echo off
chcp 65001 >nul
echo ==========================================
echo  模型性能测试平台 - 一键启动
echo ==========================================
cd /d "%~dp0"
echo.
echo [启动] FastAPI 后端服务 (端口 38081)...
start "Model-Bench-Backend" cmd /c "title 后端(38081) && venv\Scripts\python.exe -m backend.main"
echo [启动] 前端静态服务 (端口 38080)...
start "Model-Bench-Frontend" cmd /c "title 前端(38080) && cd frontend && python serve.py"
echo.
echo ==========================================
echo  后端 API: http://localhost:38081/docs
echo  前端页面: http://localhost:38080
echo ==========================================
pause >nul
