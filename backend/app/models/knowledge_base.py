from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class KnowledgeCategory(Base):
    """知识库分类表"""
    __tablename__ = "knowledge_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    description = Column(Text, comment="分类描述")
    parent_id = Column(Integer, ForeignKey("knowledge_categories.id"), nullable=True, comment="父分类ID")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关系
    parent = relationship("KnowledgeCategory", remote_side=[id], backref="children")
    knowledge_items = relationship("KnowledgeItem", back_populates="category")
    
    def __repr__(self):
        return f"<KnowledgeCategory(id={self.id}, name='{self.name}')>"

class KnowledgeTag(Base):
    """知识库标签表"""
    __tablename__ = "knowledge_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, comment="标签名称")
    color = Column(String(7), default="#007bff", comment="标签颜色(HEX)")
    description = Column(Text, comment="标签描述")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<KnowledgeTag(id={self.id}, name='{self.name}')>"

class KnowledgeItem(Base):
    """知识库条目表"""
    __tablename__ = "knowledge_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    summary = Column(Text, comment="摘要")
    keywords = Column(String(500), comment="关键词，逗号分隔")
    
    # 分类和来源
    category_id = Column(Integer, ForeignKey("knowledge_categories.id"), nullable=True, comment="分类ID")
    source_type = Column(String(50), default="manual", comment="来源类型: manual, document, web, api")
    source_file = Column(String(255), comment="源文件名")
    source_url = Column(String(500), comment="源URL")
    
    # AI分析相关
    ai_analysis = Column(JSON, comment="AI分析结果(JSON格式)")
    ai_summary = Column(Text, comment="AI生成的摘要")
    ai_keywords = Column(String(500), comment="AI提取的关键词")
    confidence_score = Column(Integer, default=0, comment="置信度分数(0-100)")
    
    # 状态和权限
    status = Column(String(20), default="draft", comment="状态: draft, published, archived")
    is_public = Column(Boolean, default=True, comment="是否公开")
    is_featured = Column(Boolean, default=False, comment="是否推荐")
    priority = Column(Integer, default=0, comment="优先级")
    
    # 统计信息
    view_count = Column(Integer, default=0, comment="查看次数")
    like_count = Column(Integer, default=0, comment="点赞次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    published_at = Column(DateTime(timezone=True), comment="发布时间")
    
    # 创建者信息
    created_by = Column(String(100), comment="创建者")
    updated_by = Column(String(100), comment="更新者")
    
    # 关系
    category = relationship("KnowledgeCategory", back_populates="knowledge_items")
    tags = relationship("KnowledgeTag", secondary="knowledge_item_tags", backref="knowledge_items")
    
    # 索引
    __table_args__ = (
        Index('idx_knowledge_items_title', 'title'),
        Index('idx_knowledge_items_category', 'category_id'),
        Index('idx_knowledge_items_status', 'status'),
        Index('idx_knowledge_items_created', 'created_at'),
        Index('idx_knowledge_items_keywords', 'keywords'),
    )
    
    def __repr__(self):
        return f"<KnowledgeItem(id={self.id}, title='{self.title[:50]}...')>"

class KnowledgeItemTag(Base):
    """知识库条目标签关联表"""
    __tablename__ = "knowledge_item_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=False)
    knowledge_tag_id = Column(Integer, ForeignKey("knowledge_tags.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 唯一约束
    __table_args__ = (
        Index('idx_unique_item_tag', 'knowledge_item_id', 'knowledge_tag_id', unique=True),
    )

class KnowledgeSearchLog(Base):
    """知识库搜索日志表"""
    __tablename__ = "knowledge_search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    search_query = Column(String(500), nullable=False, comment="搜索关键词")
    search_type = Column(String(20), default="keyword", comment="搜索类型: keyword, semantic, ai")
    results_count = Column(Integer, default=0, comment="搜索结果数量")
    user_ip = Column(String(45), comment="用户IP")
    user_agent = Column(String(500), comment="用户代理")
    response_time = Column(Integer, comment="响应时间(毫秒)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="搜索时间")
    
    # 索引
    __table_args__ = (
        Index('idx_search_logs_query', 'search_query'),
        Index('idx_search_logs_created', 'created_at'),
    )

class KnowledgeVersion(Base):
    """知识库版本历史表"""
    __tablename__ = "knowledge_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=False)
    version_number = Column(Integer, nullable=False, comment="版本号")
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    summary = Column(Text, comment="摘要")
    change_description = Column(Text, comment="变更说明")
    created_by = Column(String(100), comment="创建者")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    knowledge_item = relationship("KnowledgeItem", backref="versions")
    
    # 索引
    __table_args__ = (
        Index('idx_versions_item_version', 'knowledge_item_id', 'version_number', unique=True),
        Index('idx_versions_created', 'created_at'),
    )

class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="知识标题")
    content = Column(Text, nullable=False, comment="知识内容")
    summary = Column(Text, comment="知识摘要")
    source_file = Column(String(500), comment="来源文件")
    source_type = Column(String(50), default="document", comment="来源类型")
    tags = Column(String(500), comment="标签，逗号分隔")
    
    # 用户和状态
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者ID")
    is_active = Column(Boolean, default=True, comment="是否启用")
    view_count = Column(Integer, default=0, comment="查看次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关系
    creator = relationship("User", back_populates="knowledge_items")
    qa_records = relationship("KnowledgeQA", back_populates="knowledge_item")
    
    # 索引
    __table_args__ = (
        Index('idx_knowledge_title', 'title'),
        Index('idx_knowledge_tags', 'tags'),
        Index('idx_knowledge_created_by', 'created_by'),
        Index('idx_knowledge_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title='{self.title}')>"

class KnowledgeQA(Base):
    """知识问答记录表"""
    __tablename__ = "knowledge_qa"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=False, comment="知识ID")
    question = Column(Text, nullable=False, comment="问题")
    answer = Column(Text, nullable=False, comment="答案")
    
    # 用户和会话
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID")
    session_id = Column(String(100), comment="会话ID")
    is_guest = Column(Boolean, default=False, comment="是否游客")
    
    # 评价和统计
    is_helpful = Column(Boolean, comment="是否有帮助")
    feedback = Column(Text, comment="用户反馈")
    response_time = Column(Integer, comment="响应时间(毫秒)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    knowledge_item = relationship("KnowledgeBase", back_populates="qa_records")
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_qa_knowledge_id', 'knowledge_id'),
        Index('idx_qa_user_id', 'user_id'),
        Index('idx_qa_session_id', 'session_id'),
        Index('idx_qa_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<KnowledgeQA(id={self.id}, knowledge_id={self.knowledge_id})>"

class PresetQuestion(Base):
    """预设问题表"""
    __tablename__ = "preset_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False, comment="问题内容")
    category = Column(String(100), comment="问题分类")
    order_index = Column(Integer, default=0, comment="排序索引")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 统计
    click_count = Column(Integer, default=0, comment="点击次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_preset_category', 'category'),
        Index('idx_preset_order', 'order_index'),
    )
    
    def __repr__(self):
        return f"<PresetQuestion(id={self.id}, question='{self.question[:50]}')>" 