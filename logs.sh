#!/bin/bash

# 企业知识库智能问答系统日志查看脚本 v2.4
# 作者: 徐洪森 (lala)

echo "📜 企业知识库智能问答系统 - 日志查看工具"
echo "==========================================="
echo ""

# 检查当前目录
if [ ! -f "start.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 显示菜单
show_menu() {
    echo "🔍 日志查看选项："
    echo "   1️⃣  查看后端实时日志 (tail -f)"
    echo "   2️⃣  查看前端实时日志 (tail -f)"
    echo "   3️⃣  查看后端历史日志"
    echo "   4️⃣  查看前端历史日志"
    echo "   5️⃣  查看所有日志文件状态"
    echo "   6️⃣  清理日志文件"
    echo "   7️⃣  导出日志文件"
    echo "   8️⃣  查看系统进程状态"
    echo "   0️⃣  退出"
    echo ""
}

# 检查日志文件是否存在
check_log_file() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        local size=$(du -h "$file" | cut -f1)
        local lines=$(wc -l < "$file")
        echo "✅ $name: $file (大小: $size, 行数: $lines)"
        return 0
    else
        echo "❌ $name: $file (文件不存在)"
        return 1
    fi
}

# 查看后端实时日志
view_backend_live() {
    echo "🔍 查看后端实时日志..."
    echo "💡 按 Ctrl+C 退出实时查看"
    echo "-----------------------------------"
    
    if [ -f "backend/uvicorn.log" ]; then
        tail -f backend/uvicorn.log
    else
        echo "❌ 后端日志文件不存在: backend/uvicorn.log"
        echo "💡 请先启动后端服务"
    fi
}

# 查看前端实时日志
view_frontend_live() {
    echo "🔍 查看前端实时日志..."
    echo "💡 按 Ctrl+C 退出实时查看"
    echo "-----------------------------------"
    
    if [ -f "frontend/nextjs.log" ]; then
        tail -f frontend/nextjs.log
    else
        echo "❌ 前端日志文件不存在: frontend/nextjs.log"
        echo "💡 请先启动前端服务"
    fi
}

# 查看后端历史日志
view_backend_history() {
    echo "🔍 查看后端历史日志..."
    echo "-----------------------------------"
    
    if [ -f "backend/uvicorn.log" ]; then
        echo "📊 日志文件信息:"
        ls -lh backend/uvicorn.log
        echo ""
        echo "📜 最近50行日志:"
        echo "-----------------------------------"
        tail -50 backend/uvicorn.log
        echo ""
        echo "💡 完整日志: less backend/uvicorn.log"
    else
        echo "❌ 后端日志文件不存在: backend/uvicorn.log"
    fi
}

# 查看前端历史日志
view_frontend_history() {
    echo "🔍 查看前端历史日志..."
    echo "-----------------------------------"
    
    if [ -f "frontend/nextjs.log" ]; then
        echo "📊 日志文件信息:"
        ls -lh frontend/nextjs.log
        echo ""
        echo "📜 最近50行日志:"
        echo "-----------------------------------"
        tail -50 frontend/nextjs.log
        echo ""
        echo "💡 完整日志: less frontend/nextjs.log"
    else
        echo "❌ 前端日志文件不存在: frontend/nextjs.log"
    fi
}

# 查看所有日志文件状态
view_all_status() {
    echo "📊 所有日志文件状态:"
    echo "-----------------------------------"
    
    check_log_file "backend/uvicorn.log" "后端日志"
    check_log_file "frontend/nextjs.log" "前端日志"
    
    echo ""
    echo "📁 日志目录结构:"
    echo "-----------------------------------"
    find . -name "*.log" -type f 2>/dev/null | head -20
    
    echo ""
    echo "💾 磁盘空间使用:"
    echo "-----------------------------------"
    du -sh backend/*.log frontend/*.log 2>/dev/null || echo "暂无日志文件"
}

# 清理日志文件
clean_logs() {
    echo "🧹 清理日志文件..."
    echo "⚠️  这将删除所有日志文件，确定要继续吗？(y/N)"
    read -r confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "正在清理日志文件..."
        
        # 备份重要日志
        if [ -f "backend/uvicorn.log" ]; then
            cp backend/uvicorn.log backend/uvicorn.log.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null
        fi
        
        if [ -f "frontend/nextjs.log" ]; then
            cp frontend/nextjs.log frontend/nextjs.log.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null
        fi
        
        # 清理日志文件
        rm -f backend/uvicorn.log frontend/nextjs.log
        
        echo "✅ 日志文件已清理完成"
        echo "💾 原日志已备份为 *.backup.* 文件"
    else
        echo "❌ 取消清理操作"
    fi
}

# 导出日志文件
export_logs() {
    echo "📦 导出日志文件..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local export_dir="logs_export_$timestamp"
    
    mkdir -p "$export_dir"
    
    # 复制日志文件
    if [ -f "backend/uvicorn.log" ]; then
        cp backend/uvicorn.log "$export_dir/backend_uvicorn.log"
        echo "✅ 已导出后端日志"
    fi
    
    if [ -f "frontend/nextjs.log" ]; then
        cp frontend/nextjs.log "$export_dir/frontend_nextjs.log"
        echo "✅ 已导出前端日志"
    fi
    
    # 生成系统信息
    cat > "$export_dir/system_info.txt" << EOF
企业知识库智能问答系统 - 日志导出报告
============================================

导出时间: $(date)
系统信息: $(uname -a)
Python版本: $(python3 --version 2>/dev/null || echo "未安装")
Node.js版本: $(node --version 2>/dev/null || echo "未安装")

进程状态:
============================================
$(ps aux | grep -E "(uvicorn|next)" | grep -v grep)

端口占用:
============================================
$(lsof -i :8000 2>/dev/null || echo "端口8000未占用")
$(lsof -i :3000 2>/dev/null || echo "端口3000未占用")
EOF
    
    # 创建压缩包
    tar -czf "logs_$timestamp.tar.gz" "$export_dir"
    rm -rf "$export_dir"
    
    echo "✅ 日志导出完成: logs_$timestamp.tar.gz"
}

# 查看系统进程状态
view_process_status() {
    echo "🔍 查看系统进程状态..."
    echo "-----------------------------------"
    
    echo "📊 相关进程:"
    ps aux | grep -E "(uvicorn|next)" | grep -v grep || echo "未发现相关进程"
    
    echo ""
    echo "🌐 端口占用状态:"
    echo "后端端口 8000:"
lsof -i :8000 2>/dev/null || echo "  未占用"
    echo "前端端口 3000:"
    lsof -i :3000 2>/dev/null || echo "  未占用"
    
    echo ""
    echo "💾 系统资源使用:"
    echo "CPU使用率:"
    top -l 1 | grep "CPU usage" || echo "  无法获取"
    echo "内存使用:"
    top -l 1 | grep "PhysMem" || echo "  无法获取"
}

# 主循环
while true; do
    show_menu
    echo -n "请选择操作 [0-8]: "
    read -r choice
    echo ""
    
    case $choice in
        1)
            view_backend_live
            ;;
        2)
            view_frontend_live
            ;;
        3)
            view_backend_history
            ;;
        4)
            view_frontend_history
            ;;
        5)
            view_all_status
            ;;
        6)
            clean_logs
            ;;
        7)
            export_logs
            ;;
        8)
            view_process_status
            ;;
        0)
            echo "👋 再见！"
            exit 0
            ;;
        *)
            echo "❌ 无效选择，请输入 0-8"
            ;;
    esac
    
    echo ""
    echo "按 Enter 继续..."
    read -r
    clear
done 