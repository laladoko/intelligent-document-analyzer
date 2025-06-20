#!/bin/bash

# 前端服务启动脚本 v2.4
# 支持前台和后台运行模式

echo "🎨 启动企业知识库前端服务..."

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未找到Node.js，请先安装Node.js"
    exit 1
fi

# 安装依赖
echo "📦 安装前端依赖..."
npm install --silent

# 检查运行模式
if [ "$1" = "background" ] || [ "$1" = "bg" ]; then
    echo "🌟 启动后台模式 (端口:3000)..."
    nohup npm run dev > nextjs.log 2>&1 &
    
    echo "✅ 前端服务已启动 (PID: $!)"
    echo "📜 日志文件: nextjs.log"
    echo "🌐 访问地址: http://localhost:3000"
else
    echo "🌟 启动前台模式 (端口:3000)..."
    echo "💡 使用 'Ctrl+C' 停止服务"
    echo "💡 后台模式: ./start_frontend.sh background"
    echo "🌐 访问地址: http://localhost:3000"
    echo ""
    
    npm run dev 