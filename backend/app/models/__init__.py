from .database import Base, engine, SessionLocal, get_db
from .knowledge_base import (
    KnowledgeCategory,
    KnowledgeTag,
    KnowledgeItem,
    KnowledgeItemTag,
    KnowledgeSearchLog,
    KnowledgeVersion
)
from .schemas import (
    # 枚举类型
    SourceType,
    StatusType,
    SearchType,
    
    # 分类相关
    KnowledgeCategoryBase,
    KnowledgeCategoryCreate,
    KnowledgeCategoryUpdate,
    KnowledgeCategory as KnowledgeCategorySchema,
    
    # 标签相关
    KnowledgeTagBase,
    KnowledgeTagCreate,
    KnowledgeTagUpdate,
    KnowledgeTag as KnowledgeTagSchema,
    
    # 知识库条目相关
    KnowledgeItemBase,
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItem as KnowledgeItemSchema,
    
    # 搜索相关
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    
    # 统计相关
    KnowledgeStats,
    
    # 批量操作
    KnowledgeBatchOperation,
    KnowledgeBatchResult,
    
    # AI分析
    AIAnalysisResult,
    
    # 导入导出
    KnowledgeExportRequest,
    KnowledgeImportRequest,
    
    # 版本历史
    KnowledgeVersionBase,
    KnowledgeVersionCreate,
    KnowledgeVersion as KnowledgeVersionSchema,
)

__all__ = [
    # 数据库相关
    "Base",
    "engine", 
    "SessionLocal",
    "get_db",
    
    # 数据库模型
    "KnowledgeCategory",
    "KnowledgeTag", 
    "KnowledgeItem",
    "KnowledgeItemTag",
    "KnowledgeSearchLog",
    "KnowledgeVersion",
    
    # 枚举类型
    "SourceType",
    "StatusType", 
    "SearchType",
    
    # Pydantic模式
    "KnowledgeCategoryBase",
    "KnowledgeCategoryCreate",
    "KnowledgeCategoryUpdate", 
    "KnowledgeCategorySchema",
    "KnowledgeTagBase",
    "KnowledgeTagCreate",
    "KnowledgeTagUpdate",
    "KnowledgeTagSchema",
    "KnowledgeItemBase",
    "KnowledgeItemCreate", 
    "KnowledgeItemUpdate",
    "KnowledgeItemSchema",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "KnowledgeStats",
    "KnowledgeBatchOperation",
    "KnowledgeBatchResult",
    "AIAnalysisResult",
    "KnowledgeExportRequest",
    "KnowledgeImportRequest",
    "KnowledgeVersionBase",
    "KnowledgeVersionCreate",
    "KnowledgeVersionSchema",
]
