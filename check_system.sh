#!/bin/bash

echo "========================================="
echo "🔍 企业文档智能分析系统 - 状态检查"
echo "========================================="

# 检查端口占用
echo "📡 检查端口占用..."
echo "后端端口 8000:"
lsof -i :8000 | head -3
echo ""
echo "前端端口 3000:"
lsof -i :3000 | head -3
echo ""

# 检查进程状态
echo "🔄 检查进程状态..."
echo "后端进程:"
ps aux | grep -E "(uvicorn|python.*app.main)" | grep -v grep || echo "❌ 后端进程未运行"
echo ""
echo "前端进程:"
ps aux | grep -E "(next|node.*dev)" | grep -v grep || echo "❌ 前端进程未运行"
echo ""

# API健康检查
echo "🏥 API健康检查..."
echo -n "后端ping测试: "
if curl -m 5 -s http://localhost:8000/ping > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

echo -n "游客登录测试: "
if curl -m 5 -s -X POST http://localhost:8000/api/auth/guest-login > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

echo -n "前端页面测试: "
if curl -m 5 -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

echo ""
echo "📋 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""

# 检查最新日志
echo "📝 最新日志 (后端):"
if [ -f "backend/backend.log" ]; then
    tail -5 backend/backend.log
else
    echo "❌ 后端日志文件不存在"
fi

echo ""
echo "✅ 状态检查完成" 