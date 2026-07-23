#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python &>/dev/null && ! [ -d "venv" ]; then
    PYTHON="python"
elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
elif [ -f "venv/Scripts/python.exe" ]; then
    PYTHON="venv/Scripts/python.exe"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "[错误] 未找到 Python"; exit 1
fi

echo "=========================================="
echo " 模型性能测试平台 - 一键启动"
echo "=========================================="

echo ""
echo "[启动] FastAPI 后端服务 (端口 38081)..."
$PYTHON -m backend.main &
BACKEND_PID=$!

echo "[启动] 前端静态服务 (端口 38080)..."
cd frontend && $PYTHON serve.py &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo " 后端 API: http://localhost:38081/docs"
echo " 前端页面: http://localhost:38080"
echo "=========================================="

cleanup() {
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM
wait
