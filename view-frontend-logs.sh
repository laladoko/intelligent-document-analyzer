#!/bin/bash

# 快速查看前端日志脚本

echo "🔍 查看前端日志..."
echo "💡 按 Ctrl+C 退出"
echo "======================="

if [ -f "frontend/nextjs.log" ]; then
    tail -f frontend/nextjs.log
else
    echo "❌ 前端日志文件不存在: frontend/nextjs.log"
    echo "💡 请先启动前端服务"
    
    # 检查前端是否在运行
    if ps aux | grep "next.*dev" | grep -v grep > /dev/null; then
        echo "⚠️  前端服务正在运行，但日志文件可能在其他位置"
    else
        echo "💡 启动前端服务: cd frontend && ./start_frontend.sh"
    fi
fi 