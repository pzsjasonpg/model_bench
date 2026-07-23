#!/bin/bash
# ==========================================
#  模型性能测试平台 - 前端服务
#  用法: ./start_frontend.sh          # 本地开发
#        ./start_frontend.sh docker   # Docker 容器模式
# ==========================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/frontend"

# 检测 Python 路径
if command -v python &>/dev/null && ! [ -d "../venv" ]; then
    PYTHON="python"
elif [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
elif [ -f "../venv/Scripts/python.exe" ]; then
    PYTHON="../venv/Scripts/python.exe"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "[错误] 未找到 Python，请检查环境"
    exit 1
fi

echo "=========================================="
echo " 模型性能测试平台 - 前端服务"
echo " Python: $PYTHON"
echo "=========================================="

echo ""
echo "[启动] 前端静态服务 (端口 18080)..."
echo " 浏览器打开: http://localhost:18080"
echo ""

exec $PYTHON serve.py
