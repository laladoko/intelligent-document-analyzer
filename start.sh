#!/bin/bash

# 企业知识库智能问答系统启动脚本 v2.2
# 作者: 徐洪森 (lala)
# 更新日期: 2025-06-18

echo "========================================="
echo "企业文档智能分析和知识库问答系统 v2.2      "
echo "========================================="
echo ""
echo "更新内容:"
echo "✅ 修复了认证系统的关键问题"
echo "✅ 解决了文档上传的500错误"
echo "✅ 优化了OpenAI API调用的稳定性"
echo "✅ 修复了Next.js配置警告"
echo "✅ 增强了错误处理和日志记录"
echo ""

# 检查当前目录
if [ ! -f "start.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/uploads
mkdir -p backend/results

# 检查Python环境
echo "🐍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查Node.js环境
echo "📦 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查环境变量
echo "🔐 检查环境变量..."
if [ ! -f "backend/.env" ]; then
    echo "⚠️  警告：未找到.env文件，请确保已配置OPENAI_API_KEY"
    echo "创建示例.env文件..."
    cat > backend/.env << EOF
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./knowledge_base.db

# JWT配置
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 安全配置
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
EOF
    echo "请编辑 backend/.env 文件，填入正确的API密钥"
fi

# 启动后端服务
echo "🚀 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装后端依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️  初始化数据库..."
python init_db.py

# 启动FastAPI服务器
echo "🌟 启动FastAPI服务器 (端口:8081)..."
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 健康检查
echo "🔍 后端健康检查..."
if curl -s http://localhost:8081/ping > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 启动前端服务
echo "🎨 启动前端服务..."
cd ../frontend

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install

# 启动Next.js开发服务器
echo "🌟 启动Next.js服务器 (端口:3000)..."
npm run dev &
FRONTEND_PID=$!

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 8

# 健康检查
echo "🔍 前端健康检查..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📍 访问地址："
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8081"
echo "   API文档: http://localhost:8081/docs"
echo ""
echo "🔧 主要功能："
echo "   ✅ 企业文档智能分析 (支持PDF、DOCX、TXT)"
echo "   ✅ 文档内容自动提取和结构化"
echo "   ✅ 知识库自动构建和存储"
echo "   ✅ 智能问答和文档检索"
echo "   ✅ 多文档上下文问答"
echo "   ✅ 用户认证和权限管理"
echo "   ✅ 游客模式支持"
echo ""
echo "🛠️  使用说明："
echo "   1. 访问 http://localhost:3000 开始使用"
echo "   2. 上传企业文档进行分析"
echo "   3. 查看知识库页面管理文档"
echo "   4. 使用智能问答功能"
echo ""
echo "⚠️  注意事项："
echo "   • 请确保配置了有效的OPENAI_API_KEY"
echo "   • 支持游客模式，无需注册即可使用基本功能"
echo "   • 注册用户可享受知识库存储等高级功能"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ 服务已停止"; exit 0' INT

# 保持脚本运行
wait 