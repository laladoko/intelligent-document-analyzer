#!/bin/bash

# 企业知识库智能问答系统停止脚本 v2.5
# 作者: 徐洪森 (lala)
# 增强版 - 彻底清理所有相关进程

echo "🛑 正在停止企业知识库智能问答系统..."
echo ""

# 强制停止函数
force_kill_process() {
    local process_name=$1
    local description=$2
    
    echo "🔍 查找并停止${description}..."
    
    # 查找进程
    local pids=$(ps aux | grep "$process_name" | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$pids" ]; then
        echo "   发现${description}进程: $pids"
        
        # 先尝试优雅停止
        kill $pids 2>/dev/null
        sleep 2
        
        # 检查是否还存在
        local remaining_pids=$(ps aux | grep "$process_name" | grep -v grep | awk '{print $2}')
        if [ ! -z "$remaining_pids" ]; then
            echo "   强制终止${description}进程: $remaining_pids"
            kill -9 $remaining_pids 2>/dev/null
        fi
        
        echo "   ✅ ${description}已停止"
    else
        echo "   ℹ️  未发现运行中的${description}"
    fi
}

# 强制释放端口函数
force_release_port() {
    local port=$1
    local port_name=$2
    
    echo "🔍 检查端口${port}占用情况..."
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo "   ⚠️  端口${port}被占用，正在强制释放..."
        
        # 获取占用端口的所有进程
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            echo "   终止占用端口${port}的进程: $pids"
            kill -9 $pids 2>/dev/null
            sleep 1
        fi
        
        # 再次检查
        if lsof -i :$port > /dev/null 2>&1; then
            echo "   ⚠️  端口${port}仍被占用，尝试更强力的清理..."
            # 使用sudo强制清理（如果需要）
            sudo lsof -ti:$port | xargs sudo kill -9 2>/dev/null || true
            sleep 1
        fi
        
        # 最终检查
        if lsof -i :$port > /dev/null 2>&1; then
            echo "   ⚠️  端口${port}仍被占用，可能需要手动处理"
            echo "   占用详情:"
            lsof -i :$port | head -5
        else
            echo "   ✅ 端口${port}已释放"
        fi
    else
        echo "   ✅ 端口${port}未被占用"
    fi
}

# 停止后端服务
force_kill_process "uvicorn.*app.main" "后端服务"
force_kill_process "python.*uvicorn" "后端服务"

# 停止前端服务  
force_kill_process "next.*dev" "前端服务"
force_kill_process "node.*next" "前端服务"

# 额外的进程清理
echo "🧹 执行深度清理..."

# 清理所有可能相关的进程
pkill -f "uvicorn.*app.main" 2>/dev/null && echo "   ✅ 清理uvicorn进程" || true
pkill -f "python.*uvicorn" 2>/dev/null && echo "   ✅ 清理python uvicorn进程" || true
pkill -f "next.*dev" 2>/dev/null && echo "   ✅ 清理next dev进程" || true
pkill -f "node.*next" 2>/dev/null && echo "   ✅ 清理node next进程" || true

# 特殊处理：清理可能的僵尸进程
pkill -f "document-analyzer" 2>/dev/null || true
pkill -f "knowledge.*base" 2>/dev/null || true

echo "   ✅ 深度清理完成"

# 强制释放端口
force_release_port 8000 "后端端口"
force_release_port 3000 "前端端口"

# 清理临时文件和日志锁
echo "🗑️  清理临时文件..."
rm -f backend/*.lock 2>/dev/null || true
rm -f frontend/*.lock 2>/dev/null || true
rm -f backend/uvicorn.pid 2>/dev/null || true
rm -f frontend/next.pid 2>/dev/null || true
echo "   ✅ 临时文件清理完成"

# 最终状态检查
echo ""
echo "📊 最终状态检查..."

# 检查是否还有相关进程
remaining_backend=$(ps aux | grep -E "(uvicorn|app\.main)" | grep -v grep | wc -l)
remaining_frontend=$(ps aux | grep -E "(next.*dev|node.*next)" | grep -v grep | wc -l)

if [ $remaining_backend -eq 0 ] && [ $remaining_frontend -eq 0 ]; then
    echo "✅ 所有服务进程已彻底清理"
else
    echo "⚠️  仍有残留进程，请手动检查："
    [ $remaining_backend -gt 0 ] && echo "   后端进程: $remaining_backend 个"
    [ $remaining_frontend -gt 0 ] && echo "   前端进程: $remaining_frontend 个"
fi

# 检查端口状态
port_8000_free=$(lsof -i :8000 > /dev/null 2>&1; echo $?)
port_3000_free=$(lsof -i :3000 > /dev/null 2>&1; echo $?)

if [ $port_8000_free -eq 1 ] && [ $port_3000_free -eq 1 ]; then
    echo "✅ 所有端口已释放"
else
    echo "⚠️  端口占用状态："
    [ $port_8000_free -eq 0 ] && echo "   端口8000: 仍被占用"
    [ $port_3000_free -eq 0 ] && echo "   端口3000: 仍被占用"
fi

echo ""
echo "🎉 系统停止完成！"
echo ""
echo "💡 如需重新启动，请运行: ./start.sh"
echo "🔧 如有进程残留，请使用: sudo ./stop.sh 或手动清理"
echo "📊 检查系统状态: ./status.sh"
echo "" 