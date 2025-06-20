#!/bin/bash

# 企业知识库智能问答系统启动脚本 v2.5
# 作者: 徐洪森 (lala)
# 更新日期: 2025-06-19
# 增强版 - 改进启动稳定性

echo "========================================="
echo "企业文档智能分析和知识库问答系统 v2.5      "
echo "========================================="
echo ""
echo "🆕 v2.5 更新内容:"
echo "✅ 优化启动和停止脚本稳定性"
echo "✅ 增强端口清理和进程管理"
echo "✅ 改进前端启动逻辑"
echo "✅ 新增自动错误恢复机制"
echo "✅ 完善系统状态检查"
echo ""
echo "🔄 v2.4 功能保持:"
echo "✅ 文档删除和导出功能"
echo "✅ 流式问答输出"
echo "✅ 用户认证和权限管理"
echo "✅ 游客模式支持"
echo ""

# 检查当前目录
if [ ! -f "start.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止所有服务..."
    
    # 停止后端服务
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1
        # 如果还存在，强制终止
        kill -9 $BACKEND_PID 2>/dev/null || true
    fi
    
    # 停止前端服务
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1
        # 如果还存在，强制终止
        kill -9 $FRONTEND_PID 2>/dev/null || true
    fi
    
    # 清理可能残留的进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    
    echo "✅ 所有服务已停止"
    echo "🙏 感谢使用企业知识库智能问答系统！"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 强力端口清理函数
force_clear_port() {
    local port=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "⚠️  端口 $port 被占用 (尝试 $attempt/$max_attempts)"
            
            # 获取占用端口的进程ID
            local pids=$(lsof -ti:$port)
            if [ ! -z "$pids" ]; then
                echo "   终止进程: $pids"
                # 先尝试优雅终止
                kill $pids 2>/dev/null || true
                sleep 2
                
                # 检查是否还存在，强制终止
                local remaining_pids=$(lsof -ti:$port)
                if [ ! -z "$remaining_pids" ]; then
                    echo "   强制终止进程: $remaining_pids"
                    kill -9 $remaining_pids 2>/dev/null || true
                    sleep 1
                fi
            fi
            
            # 再次检查
            if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo "✅ 端口 $port 已释放"
                return 0
            fi
            
            attempt=$((attempt + 1))
            [ $attempt -le $max_attempts ] && sleep 2
        else
            echo "✅ 端口 $port 未被占用"
            return 0
        fi
    done
    
    echo "❌ 无法释放端口 $port，请手动处理或重启系统"
    exit 1
}

# 等待端口可用函数
wait_for_port() {
    local port=$1
    local service_name=$2
    local max_wait=30
    local wait_time=0
    
    echo "⏳ 等待${service_name}端口${port}可用..."
    
    while [ $wait_time -lt $max_wait ]; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "✅ 端口${port}已可用"
            return 0
        fi
        sleep 1
        wait_time=$((wait_time + 1))
    done
    
    echo "❌ 等待端口${port}超时"
    return 1
}

# 启动前清理
echo "🧹 启动前系统清理..."
./stop.sh > /dev/null 2>&1 || true
sleep 2

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
    echo "⚠️  警告：未找到.env文件，创建示例配置..."
    cat > backend/.env << EOF
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./knowledge_base.db

# JWT配置
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# 安全配置
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
EOF
    echo "📝 请编辑 backend/.env 文件，填入正确的OPENAI_API_KEY"
    echo ""
fi

# 强力清理端口
echo "🔍 清理端口占用..."
force_clear_port 8000
force_clear_port 3000

# 启动后端服务
echo "🚀 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
fi

# 激活虚拟环境
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 激活虚拟环境失败"
    exit 1
fi

# 更新pip
echo "📦 更新pip到最新版本..."
pip install --upgrade pip --quiet

# 安装依赖
echo "📦 安装后端依赖..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ 安装后端依赖失败"
    exit 1
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python init_db.py
if [ $? -ne 0 ]; then
    echo "❌ 数据库初始化失败"
    exit 1
fi

# 启动FastAPI服务器
echo "🌟 启动FastAPI服务器 (端口:8000)..."
nohup python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout-keep-alive 30 \
    --timeout-graceful-shutdown 10 \
    --limit-concurrency 100 \
    --limit-max-requests 1000 \
    > uvicorn.log 2>&1 &

BACKEND_PID=$!
echo "   后端进程ID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
for i in {1..20}; do
    if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
        echo "✅ 后端服务启动成功"
        break
    elif [ $i -eq 20 ]; then
        echo "❌ 后端服务启动失败，检查日志:"
        tail -10 uvicorn.log
        cleanup
        exit 1
    else
        echo "   尝试 $i/20..."
        sleep 2
    fi
done

# 健康检查
echo "🔍 后端服务健康检查..."
health_response=$(curl -s http://localhost:8000/ping 2>/dev/null)
if echo "$health_response" | grep -q "pong"; then
    echo "✅ 后端服务健康状态良好"
else
    echo "⚠️  后端服务健康检查异常，但服务可能仍然可用"
fi

# 启动前端服务
echo "🎨 启动前端服务..."
cd ../frontend

# 检查package.json
if [ ! -f "package.json" ]; then
    echo "❌ 错误：未找到package.json文件"
    cleanup
    exit 1
fi

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install --silent
if [ $? -ne 0 ]; then
    echo "❌ 安装前端依赖失败"
    cleanup
    exit 1
fi

# 确保端口3000完全可用
wait_for_port 3000 "前端" || {
    echo "❌ 前端端口不可用"
    cleanup
    exit 1
}

# 启动Next.js开发服务器
echo "🌟 启动Next.js服务器 (端口:3000)..."
# 使用nohup后台启动，并重定向输出
nohup npm run dev > nextjs.log 2>&1 &
FRONTEND_PID=$!
echo "   前端进程ID: $FRONTEND_PID"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
frontend_ready=false
for i in {1..30}; do
    # 检查进程是否还在运行
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端进程意外退出，检查日志:"
        tail -10 nextjs.log
        cleanup
        exit 1
    fi
    
    # 检查端口是否可访问
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ 前端服务启动成功"
        frontend_ready=true
        break
    fi
    
    echo "   尝试 $i/30..."
    sleep 2
done

if [ "$frontend_ready" = false ]; then
    echo "❌ 前端服务启动超时，检查日志:"
    tail -10 nextjs.log
    cleanup
    exit 1
fi

# 最终验证
echo "🔍 最终系统验证..."
backend_ok=$(curl -s http://localhost:8000/ping > /dev/null 2>&1; echo $?)
frontend_ok=$(curl -s http://localhost:3000 > /dev/null 2>&1; echo $?)

if [ $backend_ok -eq 0 ] && [ $frontend_ok -eq 0 ]; then
    echo "✅ 系统验证通过"
else
    echo "❌ 系统验证失败："
    [ $backend_ok -ne 0 ] && echo "   后端服务异常"
    [ $frontend_ok -ne 0 ] && echo "   前端服务异常"
    cleanup
    exit 1
fi

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📍 访问地址："
echo "   🌐 前端界面: http://localhost:3000"
echo "   🔗 后端API: http://localhost:8000"
echo "   📚 API文档: http://localhost:8000/docs"
echo ""
echo "👥 测试账户："
echo "   管理员：admin / admin123456"
echo "   用户：testuser / test123456"
echo "   分析师：analyst / analyst123456"
echo "   💡 或者直接点击【游客体验】免注册使用"
echo ""
echo "🔧 核心功能："
echo "   📄 企业文档智能分析 (PDF、DOCX、TXT)"
echo "   🤖 基于GPT-4o的AI内容提取"
echo "   🧠 智能知识库构建和管理"
echo "   💬 多文档上下文问答系统（支持流式输出）"
echo "   🗑️  文档删除管理 (权限控制)"
echo "   📦 批量文档导出 (ZIP格式)"
echo "   🔐 用户认证和权限管理"
echo "   👤 游客模式和注册用户双支持"
echo ""
echo "📊 系统状态："
echo "   Backend: ✅ 运行中 (PID: $BACKEND_PID)"
echo "   Frontend: ✅ 运行中 (PID: $FRONTEND_PID)"
echo "   Database: ✅ 已初始化"
echo "   OpenAI API: ✅ 兼容最新版本"
echo "   超时配置: ✅ 已优化"
echo "   流式输出: ✅ 已启用"
echo ""
echo "📜 日志管理："
echo "   ./logs.sh - 完整日志管理工具（推荐）"
echo "   ./view-backend-logs.sh - 快速查看后端日志"
echo "   ./view-frontend-logs.sh - 快速查看前端日志"
echo "   tail -f backend/uvicorn.log - 直接查看后端日志"
echo "   tail -f frontend/nextjs.log - 直接查看前端日志"
echo ""
echo "⚠️  重要说明："
echo "   🔑 请确保在backend/.env中配置有效的OPENAI_API_KEY"
echo "   🎯 游客模式：无需注册，数据不保存"
echo "   💾 注册用户：享受完整功能和数据持久化"
echo "   🗑️  删除权限：只能删除自己创建的文档（管理员除外）"
echo "   📦 导出功能：支持Markdown和XML格式的综合分析报告"
echo "   ⚡ 流式输出：实时显示AI思考和回答过程"
echo "   🔄 遇到问题可重启：Ctrl+C停止后重新运行"
echo ""
echo "🎯 技术栈："
echo "   前端: Next.js 15.1.6 + React + TypeScript + Tailwind CSS"
echo "   后端: FastAPI + Python 3.13 + SQLAlchemy"
echo "   AI引擎: OpenAI GPT-4o"
echo "   数据库: SQLite (开发) / PostgreSQL (生产)"
echo ""
echo "👨‍💻 开发者: laladoko (徐洪森)"
echo "🎯 GitHub: https://github.com/laladoko/intelligent-document-analyzer"
echo ""
echo "📝 服务管理命令："
echo "   Ctrl+C - 停止所有服务"
echo "   ./logs.sh - 查看日志管理"
echo "   ./status.sh - 检查系统状态"
echo "   ./stop.sh - 停止所有服务"
echo ""

# 保持脚本运行，等待用户中断
echo "🔄 系统运行中... 按 Ctrl+C 停止服务"
wait 