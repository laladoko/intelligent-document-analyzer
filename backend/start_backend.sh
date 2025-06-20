#!/bin/bash

# 后端服务启动脚本 v2.4
# 支持前台和后台运行模式

echo "🚀 启动企业知识库后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查后端依赖..."
pip install -r requirements.txt --quiet

# 初始化数据库
echo "🗄️  初始化数据库..."
python init_db.py

# 检查运行模式
if [ "$1" = "background" ] || [ "$1" = "bg" ]; then
    echo "🌟 启动后台模式 (端口:8000)..."
    nohup python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --timeout-keep-alive 30 \
        --timeout-graceful-shutdown 10 \
        --limit-concurrency 100 \
        --limit-max-requests 1000 \
        > uvicorn.log 2>&1 &
    
    echo "✅ 后端服务已启动 (PID: $!)"
    echo "📜 日志文件: uvicorn.log"
else
    echo "🌟 启动前台模式 (端口:8000)..."
    echo "💡 使用 'Ctrl+C' 停止服务"
    echo "💡 后台模式: ./start_backend.sh background"
    echo ""
    
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --timeout-keep-alive 30 \
        --timeout-graceful-shutdown 10 \
        --limit-concurrency 100 \
        --limit-max-requests 1000 \
        --reload 