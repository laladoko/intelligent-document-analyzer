#!/bin/bash

# 企业知识库智能问答系统状态检查脚本 v2.4
# 作者: 徐洪森 (lala)

echo "📊 企业知识库智能问答系统 - 状态检查"
echo "========================================"
echo ""

# 检查后端服务状态
check_backend() {
    echo "🔍 检查后端服务状态..."
    
    # 检查进程
    backend_pid=$(ps aux | grep "uvicorn.*app.main" | grep -v grep | awk '{print $2}')
    if [ ! -z "$backend_pid" ]; then
        echo "✅ 后端服务运行中 (PID: $backend_pid)"
        
        # 检查端口
        if lsof -i :8000 > /dev/null 2>&1; then
echo "✅ 后端端口8000正常监听"

# 健康检查
health_check=$(curl -s http://localhost:8000/ping 2>/dev/null)
            if echo "$health_check" | grep -q "pong"; then
                echo "✅ 后端API健康检查通过"
            else
                echo "⚠️  后端API健康检查失败"
            fi
        else
echo "❌ 后端端口8000未监听"
        fi
        
        # 检查日志文件
        if [ -f "backend/uvicorn.log" ]; then
            log_size=$(du -h backend/uvicorn.log | cut -f1)
            echo "📜 后端日志文件: $log_size"
        else
            echo "⚠️  后端日志文件不存在"
        fi
    else
        echo "❌ 后端服务未运行"
    fi
    echo ""
}

# 检查前端服务状态
check_frontend() {
    echo "🔍 检查前端服务状态..."
    
    # 检查进程
    frontend_pid=$(ps aux | grep "next.*dev" | grep -v grep | awk '{print $2}')
    if [ ! -z "$frontend_pid" ]; then
        echo "✅ 前端服务运行中 (PID: $frontend_pid)"
        
        # 检查端口
        if lsof -i :3000 > /dev/null 2>&1; then
            echo "✅ 前端端口3000正常监听"
            
            # 简单连接测试
            if curl -s http://localhost:3000 > /dev/null 2>&1; then
                echo "✅ 前端页面可访问"
            else
                echo "⚠️  前端页面访问异常"
            fi
        else
            echo "❌ 前端端口3000未监听"
        fi
        
        # 检查日志文件
        if [ -f "frontend/nextjs.log" ]; then
            log_size=$(du -h frontend/nextjs.log | cut -f1)
            echo "📜 前端日志文件: $log_size"
        else
            echo "⚠️  前端日志文件不存在"
        fi
    else
        echo "❌ 前端服务未运行"
    fi
    echo ""
}

# 检查系统资源
check_system() {
    echo "💾 检查系统资源..."
    
    # CPU和内存
    echo "📈 系统负载:"
    uptime
    
    echo ""
    echo "💿 磁盘使用 (项目目录):"
    du -sh . 2>/dev/null || echo "无法获取磁盘使用信息"
    
    echo ""
    echo "🗃️  日志文件大小:"
    if [ -f "backend/uvicorn.log" ] || [ -f "frontend/nextjs.log" ]; then
        du -sh backend/*.log frontend/*.log 2>/dev/null || echo "暂无日志文件"
    else
        echo "暂无日志文件"
    fi
    echo ""
}

# 检查依赖环境
check_environment() {
    echo "🔧 检查环境依赖..."
    
    # Python环境
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version)
        echo "✅ Python: $python_version"
    else
        echo "❌ Python3 未安装"
    fi
    
    # Node.js环境
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        echo "✅ Node.js: $node_version"
    else
        echo "❌ Node.js 未安装"
    fi
    
    # 虚拟环境
    if [ -d "backend/venv" ]; then
        echo "✅ Python虚拟环境已创建"
    else
        echo "⚠️  Python虚拟环境未创建"
    fi
    
    # 环境变量
    if [ -f "backend/.env" ]; then
        echo "✅ 环境变量文件存在"
    else
        echo "⚠️  环境变量文件不存在"
    fi
    
    echo ""
}

# 生成建议
generate_suggestions() {
    echo "💡 操作建议："
    
    # 检查服务状态并给出建议
    backend_running=$(ps aux | grep "uvicorn.*app.main" | grep -v grep)
    frontend_running=$(ps aux | grep "next.*dev" | grep -v grep)
    
    if [ -z "$backend_running" ] && [ -z "$frontend_running" ]; then
        echo "   🚀 启动所有服务: ./start.sh"
    elif [ -z "$backend_running" ]; then
        echo "   🔧 启动后端服务: cd backend && ./start_backend.sh"
    elif [ -z "$frontend_running" ]; then
        echo "   🎨 启动前端服务: cd frontend && ./start_frontend.sh"
    else
        echo "   ✅ 所有服务运行正常"
        echo "   📜 查看日志: ./logs.sh"
        echo "   🌐 访问系统: http://localhost:3000"
    fi
    
    echo "   🛑 停止服务: ./stop.sh"
    echo "   📊 重新检查: ./status.sh"
    echo ""
}

# 主函数
main() {
    check_backend
    check_frontend
    check_system
    check_environment
    generate_suggestions
    
    echo "📊 状态检查完成！"
    echo "更新时间: $(date)"
}

# 如果有参数，支持单独检查
if [ $# -gt 0 ]; then
    case $1 in
        backend|be)
            check_backend
            ;;
        frontend|fe)
            check_frontend
            ;;
        system|sys)
            check_system
            ;;
        env|environment)
            check_environment
            ;;
        *)
            echo "使用方法: $0 [backend|frontend|system|env]"
            echo "或直接运行 $0 进行完整检查"
            ;;
    esac
else
    main
fi 