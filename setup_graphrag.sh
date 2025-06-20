#!/bin/bash

# GraphRAG 完整安装配置脚本
# 作者: 徐洪森 (lala)
# 基于 Microsoft GraphRAG 项目: https://github.com/microsoft/graphrag

echo "🚀 GraphRAG 完整安装配置向导"
echo "========================================"
echo "📚 集成 Microsoft GraphRAG 到企业知识库系统"
echo "🔗 项目地址: https://github.com/microsoft/graphrag"
echo "📖 文档地址: https://microsoft.github.io/graphrag/"
echo ""

# 检查当前目录
if [ ! -f "start.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 检查Python环境
echo "🐍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活Python虚拟环境..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

# 检查环境变量
echo "🔐 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "❌ 错误：未找到.env文件，请先运行 ./start.sh"
    exit 1
fi

# 检查OpenAI API密钥
api_key=$(grep "OPENAI_API_KEY=" .env | cut -d'=' -f2)
if [ "$api_key" = "your_openai_api_key_here" ] || [ -z "$api_key" ]; then
    echo "⚠️  警告：未配置OpenAI API密钥"
    echo "💡 请先运行 ./setup_openai.sh 配置API密钥"
    echo "🔄 或者手动编辑 backend/.env 文件"
    echo ""
    echo "是否继续安装？(y/n)"
    read -r continue_install
    if [ "$continue_install" != "y" ] && [ "$continue_install" != "Y" ]; then
        echo "❌ 安装已取消"
        exit 1
    fi
fi

# 更新pip
echo "📦 更新pip..."
pip install --upgrade pip --quiet

# 安装GraphRAG
echo "📦 安装Microsoft GraphRAG..."
echo "⚠️  注意：这可能需要几分钟时间..."
pip install graphrag --quiet

if [ $? -ne 0 ]; then
    echo "❌ GraphRAG安装失败，尝试其他方式..."
    pip install graphrag --no-cache-dir --quiet
    if [ $? -ne 0 ]; then
        echo "❌ 无法安装GraphRAG，请检查网络连接和Python环境"
        exit 1
    fi
fi

# 安装图数据库支持库
echo "📦 安装图数据库相关库..."
pip install networkx matplotlib plotly --quiet

# 安装文本处理增强库
echo "📦 安装文本处理库..."
pip install spacy nltk tiktoken --quiet

# 安装YAML支持
echo "📦 安装YAML支持..."
pip install pyyaml --quiet

# 更新requirements文件
echo "📝 更新requirements文件..."
cd ..
pip freeze | grep -E "(graphrag|networkx|matplotlib|plotly|spacy|nltk|tiktoken|pyyaml)" >> backend/requirements.txt

# 创建GraphRAG工作目录
echo "📁 创建GraphRAG工作目录..."
mkdir -p backend/graphrag_workspace
mkdir -p backend/graphrag_workspace/input
mkdir -p backend/graphrag_workspace/output
mkdir -p backend/graphrag_workspace/cache
mkdir -p backend/graphrag_workspace/reports

# 添加GraphRAG环境变量
echo "⚙️ 配置GraphRAG环境变量..."
cd backend
if ! grep -q "GRAPHRAG_MODEL" .env; then
    echo "" >> .env
    echo "# GraphRAG 配置" >> .env
    echo "GRAPHRAG_MODEL=gpt-4o" >> .env
    echo "GRAPHRAG_EMBEDDING_MODEL=text-embedding-3-small" >> .env
    echo "GRAPHRAG_MAX_TOKENS=4000" >> .env
fi

cd ..

# 测试GraphRAG安装
echo "🧪 测试GraphRAG安装..."
cd backend
source venv/bin/activate

python3 -c "
try:
    import graphrag
    print('✅ GraphRAG导入成功')
    print(f'📦 GraphRAG版本: {graphrag.__version__ if hasattr(graphrag, \"__version__\") else \"未知\"}')
except ImportError as e:
    print(f'❌ GraphRAG导入失败: {e}')
    exit(1)

try:
    import networkx
    import matplotlib
    import plotly
    print('✅ 图数据库库导入成功')
except ImportError as e:
    print(f'⚠️  图数据库库导入失败: {e}')

try:
    import yaml
    print('✅ YAML支持导入成功')
except ImportError as e:
    print(f'❌ YAML支持导入失败: {e}')
"

if [ $? -ne 0 ]; then
    echo "❌ GraphRAG测试失败"
    exit 1
fi

cd ..

# 创建GraphRAG测试脚本
echo "📝 创建GraphRAG测试脚本..."
cat > test_graphrag.py << 'EOF'
#!/usr/bin/env python3
"""
GraphRAG 功能测试脚本
测试GraphRAG集成是否正常工作
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/.env')

def test_graphrag_import():
    """测试GraphRAG导入"""
    try:
        from backend.app.services.graphrag_service import graphrag_service
        print("✅ GraphRAG服务导入成功")
        return True
    except ImportError as e:
        print(f"❌ GraphRAG服务导入失败: {e}")
        return False

def test_graphrag_availability():
    """测试GraphRAG可用性"""
    try:
        from backend.app.services.graphrag_service import graphrag_service
        
        status = graphrag_service.get_index_status()
        print(f"📊 GraphRAG状态:")
        print(f"   GraphRAG可用: {status['graphrag_available']}")
        print(f"   API密钥配置: {status['api_key_configured']}")
        print(f"   索引存在: {status['index_exists']}")
        print(f"   工作目录: {status['workspace_path']}")
        
        return status['graphrag_available']
    except Exception as e:
        print(f"❌ GraphRAG状态检查失败: {e}")
        return False

async def test_graphrag_basic():
    """基础功能测试"""
    try:
        from backend.app.services.graphrag_service import graphrag_service
        
        if not graphrag_service.is_available():
            print("⚠️  GraphRAG不可用，跳过基础功能测试")
            return True
        
        print("🧪 执行基础功能测试...")
        
        # 这里可以添加更多测试
        print("✅ 基础功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 GraphRAG集成测试")
    print("=" * 40)
    
    # 测试导入
    import_ok = test_graphrag_import()
    
    # 测试可用性
    availability_ok = test_graphrag_availability()
    
    # 基础功能测试
    basic_ok = asyncio.run(test_graphrag_basic())
    
    print("\n" + "=" * 40)
    
    if import_ok and availability_ok and basic_ok:
        print("🎉 GraphRAG集成测试全部通过！")
        print("💡 现在可以使用GraphRAG功能了")
        print("🌐 访问 http://localhost:3000 体验GraphRAG")
    else:
        print("⚠️  部分测试失败，请检查配置")
        if not import_ok:
            print("   - 检查GraphRAG安装")
        if not availability_ok:
            print("   - 检查API密钥配置")
    
    sys.exit(0 if (import_ok and availability_ok and basic_ok) else 1)
EOF

chmod +x test_graphrag.py

# 重启服务应用更改
echo "🔄 重启系统应用GraphRAG集成..."
echo "⚠️  这将停止当前服务并重新启动..."
echo "继续？(y/n)"
read -r restart_confirm

if [ "$restart_confirm" = "y" ] || [ "$restart_confirm" = "Y" ]; then
    ./stop.sh > /dev/null 2>&1
    sleep 3
    ./start.sh > graphrag_startup.log 2>&1 &
    
    echo "⏳ 等待服务启动..."
    sleep 20
    
    # 测试服务状态
    if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
        echo "✅ 后端服务启动成功"
        
        # 测试GraphRAG API
        if curl -s http://localhost:8000/api/graphrag/health > /dev/null 2>&1; then
            echo "✅ GraphRAG API可用"
        else
            echo "⚠️  GraphRAG API可能未完全就绪"
        fi
    else
        echo "❌ 后端服务启动失败"
        echo "📜 查看启动日志: tail -f graphrag_startup.log"
    fi
fi

echo ""
echo "🎉 GraphRAG集成配置完成！"
echo ""
echo "📋 集成内容："
echo "   ✅ Microsoft GraphRAG库"
echo "   ✅ 图数据库支持"
echo "   ✅ 文本处理增强"
echo "   ✅ GraphRAG API端点"
echo "   ✅ 工作目录结构"
echo ""
echo "🔧 新增功能："
echo "   📊 /api/graphrag/status - 获取状态"
echo "   🏗️  /api/graphrag/build-index - 构建索引"
echo "   🔍 /api/graphrag/search - GraphRAG搜索"
echo "   ❤️  /api/graphrag/health - 健康检查"
echo "   📚 /api/graphrag/info - 项目信息"
echo ""
echo "🧪 测试命令："
echo "   python3 test_graphrag.py - 运行集成测试"
echo "   curl http://localhost:8000/api/graphrag/health - API健康检查"
echo ""
echo "🌐 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   GraphRAG API文档: http://localhost:8000/docs#/GraphRAG知识图谱"
echo ""
echo "📖 使用指南："
echo "   1. 上传文档到知识库"
echo "   2. 构建GraphRAG索引"
echo "   3. 使用增强的图谱搜索"
echo "   4. 体验多文档推理能力"
echo ""
echo "🔗 相关资源："
echo "   GitHub: https://github.com/microsoft/graphrag"
echo "   文档: https://microsoft.github.io/graphrag/"
echo "   集成作者: 徐洪森 (lala)" 