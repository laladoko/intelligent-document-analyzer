from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# 枚举类型定义
class SourceType(str, Enum):
    MANUAL = "manual"
    DOCUMENT = "document"
    WEB = "web"
    API = "api"

class StatusType(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class SearchType(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    AI = "ai"

# 基础模式
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 知识库分类模式
class KnowledgeCategoryBase(BaseSchema):
    name: str = Field(..., max_length=100, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否启用")

class KnowledgeCategoryCreate(KnowledgeCategoryBase):
    pass

class KnowledgeCategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class KnowledgeCategory(KnowledgeCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: List['KnowledgeCategory'] = []

# 知识库标签模式
class KnowledgeTagBase(BaseSchema):
    name: str = Field(..., max_length=50, description="标签名称")
    color: str = Field("#007bff", pattern=r"^#[0-9A-Fa-f]{6}$", description="标签颜色")
    description: Optional[str] = Field(None, description="标签描述")

class KnowledgeTagCreate(KnowledgeTagBase):
    pass

class KnowledgeTagUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = None

class KnowledgeTag(KnowledgeTagBase):
    id: int
    usage_count: int = 0
    created_at: datetime

# 知识库条目模式
class KnowledgeItemBase(BaseSchema):
    title: str = Field(..., max_length=200, description="标题")
    content: str = Field(..., description="内容")
    summary: Optional[str] = Field(None, description="摘要")
    keywords: Optional[str] = Field(None, max_length=500, description="关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    source_type: SourceType = Field(SourceType.MANUAL, description="来源类型")
    source_file: Optional[str] = Field(None, max_length=255, description="源文件名")
    source_url: Optional[str] = Field(None, max_length=500, description="源URL")
    status: StatusType = Field(StatusType.DRAFT, description="状态")
    is_public: bool = Field(True, description="是否公开")
    is_featured: bool = Field(False, description="是否推荐")
    priority: int = Field(0, description="优先级")

class KnowledgeItemCreate(KnowledgeItemBase):
    tag_ids: List[int] = Field([], description="标签ID列表")

class KnowledgeItemUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    source_type: Optional[SourceType] = None
    source_file: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)
    status: Optional[StatusType] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    priority: Optional[int] = None
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表")

class KnowledgeItem(KnowledgeItemBase):
    id: int
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    ai_keywords: Optional[str] = None
    confidence_score: int = 0
    view_count: int = 0
    like_count: int = 0
    share_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    tags: List[KnowledgeTag] = []

# 知识库搜索模式
class KnowledgeSearchRequest(BaseSchema):
    query: str = Field(..., max_length=500, description="搜索关键词")
    search_type: SearchType = Field(SearchType.KEYWORD, description="搜索类型")
    category_id: Optional[int] = Field(None, description="分类筛选")
    tag_ids: List[int] = Field([], description="标签筛选")
    status: Optional[StatusType] = Field(None, description="状态筛选")
    is_public: Optional[bool] = Field(None, description="是否公开筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

class KnowledgeSearchResponse(BaseSchema):
    items: List[KnowledgeItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    search_time: float = Field(description="搜索耗时(秒)")

# 知识库统计模式
class KnowledgeStats(BaseSchema):
    total_items: int = Field(description="总条目数")
    published_items: int = Field(description="已发布条目数")
    draft_items: int = Field(description="草稿条目数")
    total_categories: int = Field(description="总分类数")
    total_tags: int = Field(description="总标签数")
    total_views: int = Field(description="总浏览量")
    recent_items: List[KnowledgeItem] = Field(description="最近条目")
    popular_tags: List[KnowledgeTag] = Field(description="热门标签")

# 批量操作模式
class KnowledgeBatchOperation(BaseSchema):
    item_ids: List[int] = Field(..., description="条目ID列表")
    operation: str = Field(..., description="操作类型: publish, archive, delete")
    category_id: Optional[int] = Field(None, description="批量设置分类")
    tag_ids: Optional[List[int]] = Field(None, description="批量设置标签")

class KnowledgeBatchResult(BaseSchema):
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    failed_items: List[int] = Field(description="失败的条目ID")
    message: str = Field(description="操作结果消息")

# AI分析结果模式
class AIAnalysisResult(BaseSchema):
    summary: str = Field(description="AI生成摘要")
    keywords: List[str] = Field(description="AI提取关键词")
    categories: List[str] = Field(description="AI推荐分类")
    tags: List[str] = Field(description="AI推荐标签")
    confidence_score: int = Field(ge=0, le=100, description="置信度分数")
    analysis_details: Dict[str, Any] = Field(description="详细分析结果")

# 导入导出模式
class KnowledgeExportRequest(BaseSchema):
    format: str = Field("json", description="导出格式: json, csv, xml")
    category_ids: List[int] = Field([], description="导出分类")
    tag_ids: List[int] = Field([], description="导出标签")
    status: Optional[StatusType] = Field(None, description="导出状态")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")

class KnowledgeImportRequest(BaseSchema):
    format: str = Field("json", description="导入格式")
    data: str = Field(..., description="导入数据")
    merge_strategy: str = Field("skip", description="合并策略: skip, update, replace")
    default_category_id: Optional[int] = Field(None, description="默认分类")

# 版本历史模式
class KnowledgeVersionBase(BaseSchema):
    title: str = Field(..., max_length=200)
    content: str = Field(...)
    summary: Optional[str] = None
    change_description: Optional[str] = Field(None, description="变更说明")

class KnowledgeVersionCreate(KnowledgeVersionBase):
    knowledge_item_id: int

class KnowledgeVersion(KnowledgeVersionBase):
    id: int
    knowledge_item_id: int
    version_number: int
    created_by: Optional[str] = None
    created_at: datetime

# 更新前向引用
KnowledgeCategory.model_rebuild() 