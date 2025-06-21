# GraphRAG 完整使用指南

## 🎯 系统状态
- ✅ GraphRAG服务正常运行
- ✅ OpenAI API密钥已配置
- 🔄 索引正在构建中（已发现12个文档）
- 📁 工作目录：`/backend/graphrag_workspace`

## 🚀 使用方法

### 方法1：Web界面（推荐）

**访问地址**: http://localhost:3000/graphrag

#### 功能特性：
1. **状态监控面板** - 实时查看系统状态
2. **索引管理** - 构建、删除、重建索引
3. **智能搜索** - 三种搜索模式
4. **可视化界面** - 友好的用户体验

### 方法2：API调用

#### 1. 查看状态
```bash
curl -s http://localhost:8000/api/graphrag/status | python3 -m json.tool
```

#### 2. 构建索引
```bash
curl -X POST "http://localhost:8000/api/graphrag/build-index" \
  -H "Content-Type: application/json" \
  -d '{"rebuild": false}'
```

#### 3. 执行搜索（索引构建完成后）
```bash
# 全局搜索（适合概览性问题）
curl -X POST "http://localhost:8000/api/graphrag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "企业主要业务是什么？", "search_type": "global"}'

# 本地搜索（适合具体细节问题）  
curl -X POST "http://localhost:8000/api/graphrag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "具体的项目实施步骤", "search_type": "local"}'

# 混合搜索（推荐，结合全局和本地）
curl -X POST "http://localhost:8000/api/graphrag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "公司发展战略", "search_type": "hybrid"}'
```

## 📊 三种搜索模式详解

### 🌍 全局搜索 (Global Search)
- **适用场景**: 概览性问题、总结性查询
- **特点**: 从整体角度分析文档集合
- **示例问题**: 
  - "公司的主要业务领域有哪些？"
  - "企业面临的主要挑战是什么？"
  - "整体发展趋势如何？"

### 🔍 本地搜索 (Local Search)
- **适用场景**: 具体细节问题、精确查询
- **特点**: 聚焦于特定实体和关系
- **示例问题**:
  - "张三的具体职责是什么？"
  - "项目A的实施时间表"
  - "具体的技术规格要求"

### 🔄 混合搜索 (Hybrid Search)
- **适用场景**: 大多数查询（推荐）
- **特点**: 结合全局和本地搜索优势
- **示例问题**:
  - "公司在人工智能领域的布局"
  - "项目管理流程和具体实施"
  - "市场策略及执行细节"

## 🔄 索引构建过程

GraphRAG索引构建包含以下步骤：

1. **文档预处理** 📄
   - 文档分块和清理
   - 文本标准化

2. **实体提取** 🏷️
   - 识别关键实体（人名、地名、组织等）
   - 实体分类和标注

3. **关系分析** 🔗
   - 分析实体间关系
   - 构建关系图谱

4. **社区发现** 👥
   - 识别实体群组
   - 层次化聚类

5. **图谱构建** 🕸️
   - 生成知识图谱
   - 索引优化

## 📁 数据来源

### 当前文档来源
- **知识库文档**: 12个文档已发现
- **测试文档**: GraphRAG系统介绍
- **支持格式**: PDF, DOCX, TXT

### 如何添加新文档
1. 通过文档上传API添加到知识库
2. 重新构建GraphRAG索引
3. 新文档将自动集成到知识图谱

## 🚨 故障排除

### 常见问题

**索引构建缓慢**
- 原因：OpenAI API限流或网络问题
- 解决：等待自动重试，系统会处理

**搜索无结果**
- 检查索引是否构建完成
- 确认搜索查询的准确性

**API调用失败**
- 验证OpenAI API密钥配置
- 检查网络连接

### 监控命令

```bash
# 查看构建日志
tail -f backend/graphrag_workspace/logs/indexing-engine.log

# 检查输出目录
ls -la backend/graphrag_workspace/output/

# 查看系统状态
curl -s http://localhost:8000/api/graphrag/health
```

## 💡 最佳实践

### 查询优化
1. **使用自然语言**: GraphRAG支持自然语言查询
2. **选择合适的搜索模式**: 根据问题类型选择
3. **逐步细化查询**: 从宽泛到具体

### 索引管理
1. **定期更新**: 新增文档后重建索引
2. **监控性能**: 关注构建时间和资源使用
3. **备份重要数据**: 定期备份知识库

### 成本控制
1. **合理使用**: GraphRAG会消耗较多OpenAI API调用
2. **批量处理**: 一次性处理多个文档
3. **监控用量**: 关注API使用情况

## 🎯 应用场景

### 企业知识管理
- 内部文档智能检索
- 知识库问答系统
- 企业决策支持

### 学术研究
- 文献综述和分析
- 研究主题发现
- 学术观点对比

### 内容分析
- 大规模文档分析
- 主题建模和聚类
- 信息提取和总结

---

## 📞 需要帮助？

如果您在使用过程中遇到问题，可以：
1. 查看构建日志了解详细信息
2. 访问Web界面获得可视化反馈
3. 检查API响应获取错误详情

**当前状态**: 索引正在构建中，请耐心等待完成后开始使用搜索功能！ 