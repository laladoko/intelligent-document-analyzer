# 企业文档智能分析系统

基于 **GPT-4o** 的企业文档分析和 XML 生成工具，支持批量处理和综合分析。

> 🚀 **重构版本**: NextJS 15.1.6 + FastAPI + Python 3.12 + uv 包管理器  
> 👨‍💻 **开发者**: laladoko (徐洪森)  
> 🤖 **AI模型**: OpenAI GPT-4o (性价比最优)

## ✨ 主要特性

- 🎯 **现代化架构**: NextJS 15.1.6前端 + FastAPI后端 + GPT-4o AI分析
- 📄 **多格式支持**: TXT、PDF、DOCX、DOC 文件格式
- 🔄 **批量处理**: 多文件综合分析，生成单个XML报告
- 🎨 **现代化UI**: 响应式设计，支持拖拽上传
- 📊 **智能分析**: 提取企业关键信息，结构化输出
- 📁 **历史记录**: 分析记录管理和下载功能
- 🔒 **安全保护**: 完整的隐私保护配置

## 🏗️ 技术架构

### 前端 (NextJS 15.1.6)
- **框架**: Next.js 15.1.6 + React 18 + TypeScript
- **样式**: Tailwind CSS 3.4+
- **图标**: Heroicons
- **HTTP客户端**: Axios
- **端口**: 3000

### 后端 (FastAPI + Python 3.12)
- **框架**: FastAPI + Uvicorn
- **包管理**: uv (现代Python包管理器)
- **AI模型**: OpenAI GPT-4o
- **文档处理**: PyPDF2, python-docx, lxml
- **依赖管理**: requirements.in/requirements.txt 规范
- **端口**: 8081

### 开发工具
- **包管理**: uv (Python), npm (Node.js)
- **API文档**: 自动生成 Swagger UI
- **代码检查**: TypeScript, Python类型提示
- **依赖编译**: uv pip compile

## 🚀 快速开始

### 前置要求

1. **Python 3.12+** (推荐使用 Homebrew 安装)
2. **uv 包管理器**
3. **Node.js 18+** 和 npm
4. **OpenAI API Key**

### 环境设置

```bash
# 1. 安装 uv 包管理器
brew install uv

# 2. 克隆项目
git clone <repository-url>
cd dataanalays

# 3. 设置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，设置您的 OPENAI_API_KEY
```

### 启动后端 (FastAPI)

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 编译并安装依赖
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt

# 5. 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

### 启动前端 (NextJS)

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

### 访问系统

- 🌐 **前端界面**: http://localhost:3000
- 🔗 **后端API**: http://localhost:8081
- 📚 **API文档**: http://localhost:8081/docs
- 🔍 **健康检查**: http://localhost:8081/ping

## 📝 项目结构

```
dataanalays/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI 应用入口
│   │   ├── api/            # API 路由
│   │   │   ├── __init__.py
│   │   │   └── document.py # 文档分析API
│   │   ├── services/       # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   └── document_service.py
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   ├── uploads/            # 上传文件存储
│   ├── results/            # 分析结果存储
│   ├── .venv/              # Python虚拟环境
│   ├── requirements.in     # 直接依赖
│   ├── requirements.txt    # 锁定依赖
│   ├── requirements-dev.in # 开发依赖
│   └── pyproject.toml      # 项目配置
├── frontend/               # NextJS 前端
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx        # 主页面
│   ├── public/
│   ├── next.config.js      # NextJS配置
│   ├── tailwind.config.js  # Tailwind配置
│   ├── package.json
│   └── tsconfig.json
├── .gitignore
└── README.md
```

## 🔧 API 接口

### 后端API端点

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/ping` | GET | 健康检查 |
| `/docs` | GET | API文档 (Swagger UI) |
| `/api/document/upload` | POST | 单文件分析 |
| `/api/document/upload-xml` | POST | 单文件XML格式分析 |
| `/api/document/batch-upload` | POST | 批量文件分析 |
| `/api/document/batch-upload-xml` | POST | 批量文件XML格式分析 |
| `/api/document/download/{filename}` | GET | 下载结果文件 |
| `/api/document/results` | GET | 获取历史记录 |

### 请求示例

```javascript
// 单文件上传
const formData = new FormData()
formData.append('file', file)

const response = await axios.post('/api/document/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

// 批量文件上传
const formData = new FormData()
files.forEach(file => formData.append('files', file))

const response = await axios.post('/api/document/batch-upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
```

## 📊 使用功能

### 文档分析功能
1. **单文件分析**: 上传单个文档，生成详细分析报告
2. **批量综合分析**: 上传多个文档，生成综合分析XML
3. **智能信息提取**: 自动提取企业关键信息
4. **结构化输出**: 标准化XML格式输出

### 支持的分析内容
- 🏢 **公司基本信息**: 名称、成立时间等
- 🎯 **主要项目**: 项目内容、技术、成果
- 💼 **核心服务**: 服务对象、内容、特色
- 🔧 **技术方法**: 使用的技术和方法论

## 🛡️ 安全配置

项目包含完整的隐私保护配置：

### .gitignore 保护
- 环境变量文件 (`.env`)
- 上传文件目录 (`uploads/`)
- 分析结果目录 (`results/`)
- 虚拟环境目录 (`.venv/`, `venv/`)
- API密钥和敏感信息

### 环境变量
```bash
# backend/.env 文件
OPENAI_API_KEY=your_api_key_here
```

## 🔄 开发工作流

### 依赖管理
```bash
# 后端依赖更新
cd backend
# 编辑 requirements.in 添加新依赖
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt

# 前端依赖更新
cd frontend
npm install <package-name>
```

### 开发模式
```bash
# 后端开发 (支持热重载)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

# 前端开发 (支持热重载)
cd frontend
npm run dev
```

## 📈 性能特性

- ⚡ **FastAPI**: 高性能异步API框架
- 🔄 **热重载**: 开发时代码变更自动重启
- 📱 **响应式**: 支持桌面和移动设备
- 🚀 **现代化**: 使用最新的技术栈
- 🎯 **类型安全**: TypeScript + Python类型提示

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👨‍💻 作者

**laladoko (徐洪森)**
- GitHub: [@laladoko](https://github.com/laladoko)

---

⭐ 如果这个项目对您有帮助，请给它一个星标！ 