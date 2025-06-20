#!/bin/bash

echo "🔑 OpenAI API密钥配置助手"
echo "========================================="
echo ""

# 检查.env文件是否存在
if [ ! -f "backend/.env" ]; then
    echo "❌ 错误：未找到backend/.env文件"
    echo "请先运行 ./start.sh 来创建配置文件"
    exit 1
fi

echo "📝 请访问 https://platform.openai.com/api-keys 获取您的API密钥"
echo "💡 提示：您需要有OpenAI账户并充值才能使用API"
echo ""

# 读取当前API密钥
current_key=$(grep "OPENAI_API_KEY=" backend/.env | cut -d'=' -f2)

if [ "$current_key" = "your_openai_api_key_here" ]; then
    echo "⚠️  当前未配置有效的API密钥"
else
    echo "✅ 当前已配置API密钥: ${current_key:0:20}..."
fi

echo ""
echo "请输入您的OpenAI API密钥 (以sk-开头):"
read -s api_key

# 验证API密钥格式
if [[ ! $api_key =~ ^sk-.+ ]]; then
    echo ""
    echo "❌ 错误：API密钥格式不正确，应该以'sk-'开头"
    exit 1
fi

# 更新.env文件
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" backend/.env
else
    # Linux
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" backend/.env
fi

echo ""
echo "✅ API密钥配置成功！"
echo "🔄 正在重启后端服务..."

# 重启后端服务
./stop.sh > /dev/null 2>&1
sleep 2
./start.sh > startup.log 2>&1 &

echo "⏳ 等待服务启动..."
sleep 20

# 检查服务状态
if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
    echo "💡 请在网页中重新尝试文档分析功能"
else
    echo "❌ 服务启动失败，请检查日志: tail -f backend/uvicorn.log"
fi

echo ""
echo "🌐 访问地址: http://localhost:3000"
echo "📋 检查状态: ./status.sh"
echo "�� 查看日志: ./logs.sh" 