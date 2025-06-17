#!/bin/bash

# 企业文档智能分析系统 - 启动脚本
# 作者: laladoko (徐洪森)
# 架构: NextJS 15.1.6 + FastAPI + Python 3.12 + uv + PostgreSQL
# 版本: v2.1 - 优化知识库功能和搜索体验

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_feature() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

# 检查依赖
check_dependencies() {
    print_header "检查系统依赖"
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装，请先安装 Python 3.12+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | grep -o '[0-9]\+\.[0-9]\+')
    print_message "Python 版本: $(python3 --version)"
    
    # 检查 uv
    if ! command -v uv &> /dev/null; then
        print_warning "uv 未安装，正在安装..."
        if command -v brew &> /dev/null; then
            brew install uv
        else
            curl -LsSf https://astral.sh/uv/install.sh | sh
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
    fi
    
    UV_VERSION=$(uv --version 2>/dev/null || echo "未安装")
    print_message "uv 版本: $UV_VERSION"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_message "Node.js 版本: $NODE_VERSION"
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        print_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    NPM_VERSION=$(npm --version)
    print_message "npm 版本: $NPM_VERSION"
    
    # 检查 PostgreSQL（可选）
    if command -v psql &> /dev/null; then
        PSQL_VERSION=$(psql --version | head -1)
        print_message "PostgreSQL: $PSQL_VERSION"
    else
        print_warning "PostgreSQL 未检测到，如需历史记录功能请安装 PostgreSQL"
    fi
    
    print_success "所有依赖检查完成"
}

# 设置后端环境
setup_backend() {
    print_header "设置 FastAPI 后端"
    
    cd backend
    
    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env 文件不存在，从 .env.example 复制"
            cp .env.example .env
            print_warning "请编辑 backend/.env 文件，设置您的配置"
        else
            print_warning "创建 .env 文件"
            cat > .env << EOF
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=postgresql://hsx@localhost:5432/dataanalays

# JWT 配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 系统配置
DEBUG=True
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
EOF
            print_warning "请编辑 backend/.env 文件，设置您的 OPENAI_API_KEY 和其他配置"
        fi
    fi
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        print_message "创建 Python 虚拟环境..."
        uv venv
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 编译并安装依赖
    print_message "编译并安装 Python 依赖..."
    if [ -f "requirements.in" ]; then
        uv pip compile requirements.in -o requirements.txt
    fi
    uv pip install -r requirements.txt
    
    # 创建必要的目录
    mkdir -p uploads results
    
    # 检查数据库连接（可选）
    if [ -f "init_db.py" ]; then
        print_message "检查数据库连接..."
        python init_db.py 2>/dev/null && print_success "数据库连接正常" || print_warning "数据库连接失败，游客模式仍可使用"
    fi
    
    print_success "后端环境设置完成"
    cd ..
}

# 设置前端环境
setup_frontend() {
    print_header "设置 NextJS 前端"
    
    cd frontend
    
    # 检查 package.json
    if [ ! -f "package.json" ]; then
        print_error "package.json 不存在，请检查前端目录"
        exit 1
    fi
    
    # 安装依赖
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        print_message "安装 Node.js 依赖..."
        npm install
    else
        print_message "Node.js 依赖已存在，检查更新..."
        npm ci --prefer-offline
    fi
    
    # 检查 Next.js 版本
    NEXT_VERSION=$(npm list next --depth=0 2>/dev/null | grep next@ || echo "未安装")
    print_message "Next.js 版本: $NEXT_VERSION"
    
    print_success "前端环境设置完成"
    cd ..
}

# 启动后端服务
start_backend() {
    print_header "启动 FastAPI 后端服务"
    
    cd backend
    source .venv/bin/activate
    
    print_message "启动 FastAPI 服务 (端口 8081)..."
    uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload &
    BACKEND_PID=$!
    
    # 等待后端启动
    print_message "等待后端服务启动..."
    sleep 3
    
    # 检查后端是否启动成功
    for i in {1..10}; do
        if curl -s http://localhost:8081/ping > /dev/null 2>&1; then
            print_success "后端服务启动成功"
            print_message "API 文档: http://localhost:8081/docs"
            
            # 检查知识库API是否正常
            if curl -s -H "Content-Type: application/json" -X POST http://localhost:8081/api/knowledge/search -d '{"limit":1}' > /dev/null 2>&1; then
                print_success "知识库搜索API正常"
            else
                print_warning "知识库搜索API可能需要认证"
            fi
            break
        elif [ $i -eq 10 ]; then
            print_error "后端服务启动失败，请检查日志"
            exit 1
        else
            sleep 1
        fi
    done
    
    cd ..
}

# 启动前端服务
start_frontend() {
    print_header "启动 NextJS 前端服务"
    
    cd frontend
    
    print_message "启动 NextJS 服务..."
    npm run dev &
    FRONTEND_PID=$!
    
    # 等待前端启动
    print_message "等待前端服务启动..."
    sleep 5
    
    # 检查前端是否启动成功
    for i in {1..15}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "前端服务启动成功"
            print_message "前端界面: http://localhost:3000"
            break
        elif curl -s http://localhost:3001 > /dev/null 2>&1; then
            print_success "前端服务启动成功"
            print_message "前端界面: http://localhost:3001 (端口3000被占用)"
            break
        elif curl -s http://localhost:3002 > /dev/null 2>&1; then
            print_success "前端服务启动成功"
            print_message "前端界面: http://localhost:3002 (端口3000-3001被占用)"
            break
        elif [ $i -eq 15 ]; then
            print_error "前端服务启动失败，请检查日志"
            exit 1
        else
            sleep 1
        fi
    done
    
    cd ..
}

# 显示启动信息
show_startup_info() {
    print_header "🚀 企业文档智能分析系统已启动"
    echo ""
    echo -e "${GREEN}📱 前端界面:${NC} http://localhost:3000 (自动适配端口)"
    echo -e "${GREEN}🔗 后端API:${NC} http://localhost:8081"
    echo -e "${GREEN}📚 API文档:${NC} http://localhost:8081/docs"
    echo -e "${GREEN}🧠 知识库问答:${NC} http://localhost:3000/knowledge"
    echo -e "${GREEN}🔍 健康检查:${NC} http://localhost:8081/ping"
    echo ""
    echo -e "${CYAN}🎯 核心功能:${NC}"
    echo "  📄 支持多种文档格式 (TXT, PDF, DOCX, DOC)"
    echo "  🤖 基于 GPT-4o 的智能AI分析"
    echo "  🧠 企业知识库智能问答系统"
    echo "  📊 提供文本和XML结构化输出"
    echo "  💾 用户数据持久化存储"
    echo "  🔒 JWT认证和用户管理"
    echo ""
    print_feature "🆕 智能知识库问答系统"
    echo "  📚 文档分析结果自动存储到知识库"
    echo "  🤖 基于企业知识的智能问答"
    echo "  ❓ 预设企业管理相关热门问题"
    echo "  🔍 支持知识搜索和标签筛选"
    echo "  ✨ 自动显示用户上传的文档"
    echo "  🔧 修复了搜索API的422错误"
    echo ""
    print_feature "🆕 游客登录体验模式"
    echo "  👤 无需注册即可体验完整功能"
    echo "  ⚡ 数据存储在浏览器会话中"
    echo "  🔄 页面刷新后数据自动清空"
    echo "  💡 完美的产品试用体验"
    echo ""
    echo -e "${YELLOW}💡 使用说明:${NC}"
    echo "  1. 打开浏览器访问前端界面"
    echo "  2. 选择【游客体验】或【用户登录】"
    echo "  3. 上传企业文档进行智能分析 (自动加入知识库)"
    echo "  4. 选择输出格式 (普通文本 / XML结构化)"
    echo "  5. 查看AI分析结果并下载文件"
    echo "  6. 访问知识库问答页面查看上传的文档"
    echo "  7. 在知识库中进行基于文档的智能问答"
    echo "  8. 游客模式数据不保存，注册用户可查看历史"
    echo ""
    echo -e "${BLUE}⚡ 技术栈:${NC}"
    echo "  🔸 前端: NextJS 15.1.6 + React + TypeScript + Tailwind CSS"
    echo "  🔸 后端: FastAPI + Python 3.12 + SQLAlchemy + Alembic"
    echo "  🔸 数据库: PostgreSQL + JWT认证"
    echo "  🔸 AI引擎: OpenAI GPT-4o"
    echo "  🔸 包管理: uv (Python) + npm (Node.js)"
    echo ""
    echo -e "${PURPLE}👨‍💻 开发者:${NC} laladoko (徐洪森)"
    echo -e "${PURPLE}🎯 GitHub:${NC} https://github.com/laladoko"
    echo ""
    echo -e "${CYAN}🔄 v2.1 更新内容:${NC}"
    echo "  ✅ 修复知识库搜索API的422错误"
    echo "  ✅ 优化文档自动显示功能"
    echo "  ✅ 改进登录后重定向逻辑"
    echo "  ✅ 增强用户体验和错误处理"
    echo ""
    echo -e "${RED}⚠️  按 Ctrl+C 停止所有服务${NC}"
    echo ""
}

# 清理函数
cleanup() {
    echo ""
    print_header "正在停止服务..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_message "后端服务已停止"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_message "前端服务已停止"
    fi
    
    # 杀死可能残留的进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    
    print_success "所有服务已停止"
    echo -e "${BLUE}感谢使用企业文档智能分析系统！${NC}"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 显示帮助信息
show_help() {
    echo "企业文档智能分析系统 - 启动脚本 v2.1"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --no-frontend  只启动后端服务"
    echo "  --no-backend   只启动前端服务"
    echo "  --dev         开发模式 (详细日志)"
    echo ""
    echo "新功能:"
    echo "  📚 文档自动保存到知识库"
    echo "  🔍 优化的搜索和显示功能"
    echo "  🔧 修复了API错误问题"
    echo "  ✨ 改进的用户体验"
    echo ""
    echo "示例:"
    echo "  $0                # 启动完整系统"
    echo "  $0 --no-frontend  # 只启动后端API"
    echo "  $0 --no-backend   # 只启动前端界面"
}

# 主函数
main() {
    # 解析命令行参数
    NO_FRONTEND=false
    NO_BACKEND=false
    DEV_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --no-frontend)
                NO_FRONTEND=true
                shift
                ;;
            --no-backend)
                NO_BACKEND=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header "🚀 企业文档智能分析系统启动脚本"
    echo -e "${PURPLE}版本: v2.1 (优化知识库功能和搜索体验)${NC}"
    echo ""
    
    check_dependencies
    
    if [ "$NO_BACKEND" = false ]; then
        setup_backend
        start_backend
    fi
    
    if [ "$NO_FRONTEND" = false ]; then
        setup_frontend
        start_frontend
    fi
    
    show_startup_info
    
    # 保持脚本运行
    wait
}

# 运行主函数
main "$@" 