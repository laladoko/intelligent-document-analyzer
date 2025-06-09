# 智能文档分析系统

一个基于Flask和OpenAI的智能文档分析系统，支持单文件和多文件综合分析，自动生成XML格式的分析报告。

## ✨ 功能特点

- 📄 **多格式支持**：支持 TXT、PDF、DOCX 文件上传分析
- 🤖 **AI 智能分析**：使用 OpenAI GPT-4 进行企业文档内容分析
- 📊 **多文件综合分析**：将多个文件内容合并分析，生成单个综合报告
- 📋 **XML 格式输出**：结构化的分析结果，便于后续处理
- 🎨 **现代化界面**：基于 Bootstrap 5 的响应式设计
- 📁 **历史记录管理**：查看和下载历史分析结果
- 🏢 **企业级分析**：专门针对企业文档进行关键信息提取和整理

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/dataanalays.git
cd dataanalays
```

### 2. 创建虚拟环境

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，添加您的 OpenAI API 密钥
# OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 运行应用

```bash
python app.py
```

访问 http://localhost:8080 开始使用！

## 📋 系统要求

- Python 3.11+ (推荐)
- OpenAI API 密钥
- 16MB 以下的文档文件

## 🔧 技术栈

- **后端**：Flask 3.0.0
- **AI**：OpenAI GPT-4
- **文档处理**：PyPDF2, python-docx
- **XML 处理**：lxml
- **前端**：Bootstrap 5, Font Awesome
- **部署**：支持多种部署方式

## 📖 使用说明

### 企业文档分析
本系统专门针对企业文档进行智能分析，自动提取关键企业信息：

**分析内容包括：**
- 🏢 企业历史及背景
- 📋 主要完成的项目及成果  
- 🛠️ 核心产品及服务内容

**输出格式：**
```
公司名称：[从文档中提取]
成立时间：[从文档中提取]
主要项目：[项目列表和成果]
核心产品与服务：[产品服务描述]
```

### 单文件分析
1. 选择或拖拽单个企业文档到上传区域
2. 系统使用GPT-4分析并生成结构化企业信息XML报告
3. 下载分析结果

### 多文件综合分析
1. 选择或拖拽多个企业文档到上传区域（如：公司介绍、项目报告、产品手册等）
2. 查看文件列表，确认要分析的文件
3. 点击"综合分析生成单个XML"按钮
4. 系统将所有文件内容合并分析，生成一个企业综合信息报告
5. 下载综合分析结果

### XML 报告格式

**单文件分析**：
```xml
<document_analysis>
  <metadata>...</metadata>
  <original_content>...</original_content>
  <ai_analysis>...</ai_analysis>
</document_analysis>
```

**多文件综合分析**：
```xml
<batch_document_analysis>
  <metadata>...</metadata>
  <source_files>...</source_files>
  <comprehensive_analysis>...</comprehensive_analysis>
</batch_document_analysis>
```

## 🔒 隐私和安全

- ✅ 上传的文件仅在分析过程中临时保存，分析完成后自动删除
- ✅ 生成的XML结果文件保存在本地`results/`目录
- ✅ API密钥通过环境变量管理，不会暴露在代码中
- ✅ 支持本地部署，数据不会离开您的服务器

## 📁 项目结构

```
dataanalays/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── .gitignore            # Git 忽略文件
├── README.md             # 项目说明
├── templates/
│   └── index.html        # 前端页面
├── uploads/              # 临时上传目录 (已忽略)
└── results/              # 分析结果目录 (已忽略)
```

## ⚠️ 注意事项

1. **API 配额**：使用 OpenAI API 会产生费用，请注意控制使用量
2. **文件大小**：单个文件最大支持 16MB
3. **文件格式**：目前仅支持 TXT、PDF、DOCX 格式
4. **Python 版本**：推荐使用 Python 3.11，避免依赖包兼容性问题

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [OpenAI API 文档](https://platform.openai.com/docs)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Bootstrap 5 文档](https://getbootstrap.com/) 