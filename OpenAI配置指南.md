# OpenAI API 配置指南

## 重要更新

系统已将模拟的OpenAI接口替换为真实的OpenAI API调用，现在需要配置有效的API密钥才能使用文档分析功能。

## 配置方法

### 方法1：环境变量配置（推荐）

#### macOS/Linux系统：
```bash
# 临时设置（当前终端会话有效）
export OPENAI_API_KEY="your_actual_api_key_here"

# 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export OPENAI_API_KEY="your_actual_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows系统：
```cmd
# 临时设置
set OPENAI_API_KEY=your_actual_api_key_here

# 永久设置（系统环境变量）
在系统环境变量中添加：
变量名：OPENAI_API_KEY
变量值：your_actual_api_key_here
```

### 方法2：.env文件配置

在 `backend` 目录下创建 `.env` 文件：
```env
OPENAI_API_KEY=your_actual_api_key_here
```

## 获取OpenAI API密钥

1. 访问 [OpenAI平台](https://platform.openai.com/)
2. 登录或注册账户
3. 进入 API Keys 页面
4. 点击 "Create new secret key"
5. 复制生成的API密钥

## 验证配置

运行以下命令验证配置是否正确：

```bash
cd backend
source venv/bin/activate
python -c "import os; print('API密钥已配置：', bool(os.getenv('OPENAI_API_KEY')))"
```

## 功能说明

配置完成后，以下功能将使用真实的OpenAI API：

### 文档分析功能
- **模型**: GPT-4o
- **分析类型**: 企业文档智能分析
- **输出格式**: 结构化文本和XML格式
- **超时设置**: 150秒
- **重试机制**: 最多3次重试

### API限流处理
- 自动检测API限流
- 智能重试机制
- 渐进式延迟重试

### 错误处理
- API密钥验证
- 超时检测和处理  
- 详细错误日志记录

## 注意事项

1. **API费用**: 使用真实API会产生费用，请注意使用量
2. **安全性**: 不要将API密钥提交到版本控制系统
3. **性能**: 真实API调用比模拟慢，请耐心等待
4. **限流**: OpenAI有API调用频率限制，请合理使用

## 故障排除

### 常见错误

**错误**: `请设置 OPENAI_API_KEY 环境变量`
**解决**: 按照上述方法设置环境变量

**错误**: `OpenAI API限流，请稍后重试`
**解决**: 等待几分钟后重试，或升级API配额

**错误**: `OpenAI API调用超时`
**解决**: 检查网络连接，或减少文档长度

### 检查命令

```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 检查API连接
cd backend
source venv/bin/activate
python -c "
import os
import openai
try:
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print('OpenAI客户端创建成功')
except Exception as e:
    print(f'错误: {e}')
"
```

## 支持的功能

- ✅ 单文档智能分析
- ✅ 批量文档分析  
- ✅ XML格式输出
- ✅ 多种文档格式支持（PDF、DOCX、TXT）
- ✅ 自动重试和错误处理
- ✅ 企业级分析格式

配置完成后，您就可以享受完整的AI文档分析功能了！ 