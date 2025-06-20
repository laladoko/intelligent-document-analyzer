#!/bin/bash

# GraphRAG 集成安装脚本
# 作者: 徐洪森 (lala)
# 基于 Microsoft GraphRAG 项目

echo "🚀 GraphRAG 集成安装脚本"
echo "========================================"
echo "项目地址: https://github.com/microsoft/graphrag"
echo "文档地址: https://microsoft.github.io/graphrag/"
echo ""

# 检查当前目录
if [ ! -f "start.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活Python虚拟环境..."
cd backend
source venv/bin/activate

# 安装GraphRAG
echo "📦 安装Microsoft GraphRAG..."
pip install graphrag

# 安装图数据库支持 (可选)
echo "📦 安装图数据库相关库..."
pip install networkx matplotlib plotly

# 安装文本处理增强库
echo "📦 安装文本处理库..."
pip install spacy nltk

# 创建GraphRAG工作目录
echo "📁 创建GraphRAG工作目录..."
mkdir -p graphrag_workspace
mkdir -p graphrag_workspace/input
mkdir -p graphrag_workspace/output
mkdir -p graphrag_workspace/config

# 初始化GraphRAG配置
echo "⚙️ 初始化GraphRAG配置..."
cd graphrag_workspace
python -m graphrag.index --init --root .

# 返回到项目根目录
cd ../..

echo ""
echo "✅ GraphRAG安装完成！"
echo ""
echo "📋 下一步："
echo "   1. 配置OpenAI API密钥"
echo "   2. 运行 ./setup_graphrag.sh 进行详细配置"
echo "   3. 重启系统: ./stop.sh && ./start.sh"
echo ""
echo "🔗 更多信息："
echo "   GitHub: https://github.com/microsoft/graphrag"
echo "   文档: https://microsoft.github.io/graphrag/" 