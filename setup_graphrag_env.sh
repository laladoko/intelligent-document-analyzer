#!/bin/bash

# GraphRAG 环境配置脚本
# 开发者: 徐洪森 (laladoko)
# 版本: 1.0

echo "========================================="
echo "GraphRAG 环境配置工具 v1.0"
echo "========================================="
echo ""

# 检查当前目录
if [ ! -f "setup_graphrag_env.sh" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 环境变量文件路径
ENV_FILE="backend/.env"
ENV_EXAMPLE="backend/.env.example"

echo "🔍 检查环境变量文件..."

# 如果.env文件不存在，从示例文件复制
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo "📝 从示例文件创建环境变量文件..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
    else
        echo "❌ 错误：未找到环境变量示例文件"
        exit 1
    fi
fi

# 检查OpenAI API Key
echo ""
echo "🔑 检查OpenAI API密钥配置..."

current_key=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2-)

if [ "$current_key" = "your_openai_api_key_here" ] || [ -z "$current_key" ]; then
    echo "⚠️  需要配置OpenAI API密钥"
    echo ""
    echo "请输入您的OpenAI API密钥 (或按Enter跳过):"
    read -r api_key
    
    if [ ! -z "$api_key" ]; then
        # 更新API密钥
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" "$ENV_FILE"
        else
            # Linux
            sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" "$ENV_FILE"
        fi
        echo "✅ API密钥已更新"
    else
        echo "⚠️  跳过API密钥配置，请稍后手动编辑 $ENV_FILE"
    fi
else
    echo "✅ API密钥已配置"
fi

# 显示GraphRAG配置选项
echo ""
echo "🔧 GraphRAG配置选项:"
echo ""
echo "当前配置:"
echo "  模型: $(grep "^GRAPHRAG_MODEL=" "$ENV_FILE" | cut -d'=' -f2-)"
echo "  嵌入模型: $(grep "^GRAPHRAG_EMBEDDING_MODEL=" "$ENV_FILE" | cut -d'=' -f2-)"
echo "  并发请求: $(grep "^GRAPHRAG_CONCURRENT_REQUESTS=" "$ENV_FILE" | cut -d'=' -f2-)"
echo "  TPM限制: $(grep "^GRAPHRAG_TPM=" "$ENV_FILE" | cut -d'=' -f2-)"
echo "  RPM限制: $(grep "^GRAPHRAG_RPM=" "$ENV_FILE" | cut -d'=' -f2-)"

echo ""
echo "💡 配置建议："
echo "  - 如果您有GPT-4访问权限，建议使用 gpt-4o 模型"
echo "  - 如果API限制较低，可以降低 TPM 和 RPM 值"
echo "  - 嵌入模型建议使用 text-embedding-3-small (性价比高)"

echo ""
echo "是否要修改GraphRAG配置? (y/N):"
read -r modify_config

if [[ "$modify_config" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔧 修改GraphRAG配置..."
    
    echo "选择模型 (当前: $(grep "^GRAPHRAG_MODEL=" "$ENV_FILE" | cut -d'=' -f2-)):"
    echo "1) gpt-4o (推荐)"
    echo "2) gpt-4"
    echo "3) gpt-3.5-turbo"
    echo "4) 保持当前"
    read -r model_choice
    
    case $model_choice in
        1)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-4o/" "$ENV_FILE"
            else
                sed -i "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-4o/" "$ENV_FILE"
            fi
            echo "✅ 模型已设置为 gpt-4o"
            ;;
        2)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-4/" "$ENV_FILE"
            else
                sed -i "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-4/" "$ENV_FILE"
            fi
            echo "✅ 模型已设置为 gpt-4"
            ;;
        3)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-3.5-turbo/" "$ENV_FILE"
            else
                sed -i "s/^GRAPHRAG_MODEL=.*/GRAPHRAG_MODEL=gpt-3.5-turbo/" "$ENV_FILE"
            fi
            echo "✅ 模型已设置为 gpt-3.5-turbo"
            ;;
        *)
            echo "保持当前模型配置"
            ;;
    esac
fi

# 创建GraphRAG工作空间
echo ""
echo "📁 创建GraphRAG工作空间..."
mkdir -p backend/graphrag_workspace/{input,output,cache,reports,prompts}

# 检查GraphRAG工作空间
workspace_path="backend/graphrag_workspace"
if [ -d "$workspace_path" ]; then
    echo "✅ GraphRAG工作空间已创建: $workspace_path"
    echo "   📁 input/    - 输入文档目录"
    echo "   📁 output/   - 索引输出目录"
    echo "   📁 cache/    - 缓存目录"
    echo "   📁 reports/  - 报告目录"
    echo "   📁 prompts/  - 提示词目录"
else
    echo "❌ 工作空间创建失败"
fi

# 显示下一步操作
echo ""
echo "🎉 GraphRAG环境配置完成！"
echo ""
echo "📝 下一步操作："
echo "1. 确保您的OpenAI API密钥有效且有足够额度"
echo "2. 重启后端服务: ./stop.sh && ./start.sh"
echo "3. 访问 http://localhost:3000/graphrag"
echo "4. 上传文档并构建GraphRAG索引"
echo ""
echo "🔍 配置文件位置:"
echo "   环境变量: $ENV_FILE"
echo "   工作空间: $workspace_path"
echo ""
echo "💡 提示："
echo "   - 构建索引可能需要几分钟到几十分钟"
echo "   - 确保网络连接稳定"
echo "   - 监控API使用额度"
echo ""
echo "👨‍💻 开发者: laladoko (徐洪森)"
echo "🎯 GitHub: https://github.com/laladoko" 