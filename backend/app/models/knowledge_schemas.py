from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .auth_schemas import BaseSchema

# 知识库相关模式
class KnowledgeBaseCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200, description="知识标题")
    content: str = Field(..., min_length=1, description="知识内容")
    summary: Optional[str] = Field(None, description="知识摘要")
    source_file: Optional[str] = Field(None, max_length=500, description="来源文件")
    source_type: str = Field("document", max_length=50, description="来源类型")
    tags: Optional[str] = Field(None, max_length=500, description="标签，逗号分隔")

class KnowledgeBaseUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class KnowledgeBase(BaseSchema):
    id: int
    title: str
    content: str
    summary: Optional[str] = None
    source_file: Optional[str] = None
    source_type: str
    tags: Optional[str] = None
    created_by: int
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class KnowledgeBaseList(BaseSchema):
    id: int
    title: str
    summary: Optional[str] = None
    source_file: Optional[str] = None
    tags: Optional[str] = None
    view_count: int
    created_at: datetime

# 问答相关模式
class KnowledgeQACreate(BaseSchema):
    question: str = Field(..., min_length=1, description="问题")
    knowledge_ids: Optional[List[int]] = Field(None, description="相关知识ID列表")

class KnowledgeQAResponse(BaseSchema):
    id: int
    question: str
    answer: str
    knowledge_id: Optional[int] = None
    session_id: Optional[str] = None
    is_guest: bool
    response_time: Optional[int] = None
    created_at: datetime

class KnowledgeQAFeedback(BaseSchema):
    qa_id: int = Field(..., description="问答记录ID")
    is_helpful: bool = Field(..., description="是否有帮助")
    feedback: Optional[str] = Field(None, max_length=1000, description="用户反馈")

# 预设问题相关模式
class PresetQuestionCreate(BaseSchema):
    question: str = Field(..., min_length=1, max_length=500, description="问题内容")
    category: Optional[str] = Field(None, max_length=100, description="问题分类")
    order_index: int = Field(0, description="排序索引")

class PresetQuestionUpdate(BaseSchema):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class PresetQuestion(BaseSchema):
    id: int
    question: str
    category: Optional[str] = None
    order_index: int
    is_active: bool
    click_count: int
    created_at: datetime

# 搜索和查询相关模式
class KnowledgeSearchRequest(BaseSchema):
    query: Optional[str] = Field(None, max_length=200, description="搜索关键词")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    source_type: Optional[str] = Field(None, description="来源类型筛选")
    limit: int = Field(10, ge=1, le=50, description="返回数量限制")

class KnowledgeSearchResult(BaseSchema):
    knowledge_items: List[KnowledgeBaseList]
    total: int
    query: str

# 知识库统计模式
class KnowledgeStats(BaseSchema):
    total_knowledge: int = Field(description="知识总数")
    total_qa: int = Field(description="问答总数")
    active_knowledge: int = Field(description="活跃知识数")
    popular_tags: List[str] = Field(description="热门标签")
    recent_questions: List[str] = Field(description="最近问题")

# 批量操作模式
class KnowledgeBatchCreate(BaseSchema):
    items: List[KnowledgeBaseCreate] = Field(..., max_items=50, description="批量创建的知识项")

class KnowledgeBatchResponse(BaseSchema):
    created_count: int
    failed_count: int
    created_ids: List[int]
    errors: List[str]

# 导出模式
class KnowledgeExportRequest(BaseSchema):
    knowledge_ids: Optional[List[int]] = Field(None, description="指定知识ID列表")
    tags: Optional[List[str]] = Field(None, description="按标签导出")
    format: str = Field("json", pattern="^(json|csv|xml)$", description="导出格式")
    include_qa: bool = Field(False, description="是否包含问答记录")

class KnowledgeExportResponse(BaseSchema):
    download_url: str
    filename: str
    total_items: int
    export_format: str 