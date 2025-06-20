#!/bin/bash

# 快速查看后端日志脚本

echo "🔍 查看后端日志..."
echo "💡 按 Ctrl+C 退出"
echo "======================="

if [ -f "backend/uvicorn.log" ]; then
    tail -f backend/uvicorn.log
else
    echo "❌ 后端日志文件不存在: backend/uvicorn.log"
    echo "💡 请先启动后端服务"
    
    # 检查后端是否在运行
    if ps aux | grep "uvicorn.*app.main" | grep -v grep > /dev/null; then
        echo "⚠️  后端服务正在运行，但日志文件可能在其他位置"
    else
        echo "💡 启动后端服务: cd backend && ./start_backend.sh"
    fi
fi 